##----------------------------------------------------------------------------##
##---- puck task -------------------------------------------------------------##
##----------------------------------------------------------------------------##
## HID puck version of the puck task class - try to make it similar.

class PuckTask(object):
    degrees_of_freedom = {'r':0, 'p': 1, 'y': 2}
    def __init__(self, dof='p'):
        self.dof = self.degrees_of_freedom[dof]  # we actually want the index
        self.state = 0
        self.pos_reference = 0
        self.target = 15

    def checkStateATrigger(self, rehab_touch):
        if self.state == 1: return
        pos = rehab_touch.puck_packet_1.roll_pitch_yaw[0,self.dof]
        if not pos: return
        if (pos - self.pos_reference) < -self.target:
            self.state = 1
            return True

        return False

    def checkStateBTrigger(self, rehab_touch):
        if self.state == 0: return
        pos = rehab_touch.puck_packet_1.roll_pitch_yaw[0,self.dof]
        if not pos: return
        if (pos - self.pos_reference) > self.target:
            self.state = 0
            return True
        return False
