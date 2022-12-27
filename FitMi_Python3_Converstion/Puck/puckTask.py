##----------------------------------------------------------------------------##
##---- puck task -------------------------------------------------------------##
##----------------------------------------------------------------------------##
## HID puck version of the puck task class - try to make it similar.

class PuckTask(object):
    DOFS = {'r':0, 'p': 1, 'y': 2}
    def __init__(self, dof='p'):
        self.dof = self.DOFS[dof]  # we actually want the index
        self.state = 0
        self.pos_reference = 0
        self.target = 15

    def checkStateATrigger(self, rehabtouch):
        if self.state == 1: return
        pos = rehabtouch.puckpack1.rpy[0,self.dof]
        if not pos: return
        if (pos - self.pos_reference) < -self.target:
            self.state = 1
            return True

        return False

    def checkStateBTrigger(self, rehabtouch):
        if self.state == 0: return
        pos = rehabtouch.puckpack1.rpy[0,self.dof]
        if not pos: return
        if (pos - self.pos_reference) > self.target:
            self.state = 0
            return True
        return False
