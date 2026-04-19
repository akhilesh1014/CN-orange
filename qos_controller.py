from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp

class QoSController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(QoSController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}  # MAC learning table: {dpid: {mac: port}}

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath, buffer_id=buffer_id,
                priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath, priority=priority,
                match=match, instructions=inst)

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Table-miss rule: send unknown packets to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        self.logger.info("Switch connected: dpid=%s", datapath.id)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        # Learn source MAC -> port mapping
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # Determine output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install a flow rule only for IP traffic 
        if out_port != ofproto.OFPP_FLOOD:
            ip = pkt.get_protocol(ipv4.ipv4)
            if ip:
                if ip.proto == 17:  # UDP — high priority
                    match = parser.OFPMatch(
                        in_port=in_port, eth_dst=dst,
                        eth_type=0x0800, ip_proto=17)
                    priority = 100
                    self.logger.info("UDP flow installed: %s -> %s (priority 100)", src, dst)
                elif ip.proto == 6:  # TCP — low priority
                    match = parser.OFPMatch(
                        in_port=in_port, eth_dst=dst,
                        eth_type=0x0800, ip_proto=6)
                    priority = 10
                    self.logger.info("TCP flow installed: %s -> %s (priority 10)", src, dst)
                else:  # ICMP or other IP — use protocol-specific match
                    match = parser.OFPMatch(
                        in_port=in_port, eth_dst=dst,
                        eth_type=0x0800, ip_proto=ip.proto)
                    priority = 1

                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.add_flow(datapath, priority, match, actions, msg.buffer_id)
                    return
                else:
                    self.add_flow(datapath, priority, match, actions)
            # ARP: just forward, don't install a flow rule
            # so future IP packets always reach the controller for QoS treatment

        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id,
            in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
