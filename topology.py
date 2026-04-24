from mininet.topo import Topo

class CustomTopo(Topo):
    def build(self):

        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')

        # Add switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')

        # Connect hosts
        self.addLink(h1, s1)
        self.addLink(h2, s3)
        self.addLink(h3, s5)
        self.addLink(h4, s2)
        self.addLink(h5, s4)

        # Backbone with constraints (IMPORTANT)
        self.addLink(s1, s2, bw=1, delay='10ms')
        self.addLink(s2, s3, bw=1, delay='10ms')
        self.addLink(s3, s4, bw=1, delay='10ms')
        self.addLink(s4, s5, bw=1, delay='10ms')

# Register topology
topos = {'customtopo': (lambda: CustomTopo())}
