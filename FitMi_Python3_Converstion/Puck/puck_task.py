from Puck.hid_puck import HIDPuckDongle


class PuckTask(object):
    '''
    Attributes
    ----------
    degrees_of_freedom : dict
        Dictionary of the roll, pitch, and yaw of the puck
    dof : string
        index to the roll_pitch_yaw variable of the yellow puck
    state : bool
        state for if the yellow puck's desired degree of freedom is less than
        the negative of the target value (True) or greater than the target
        value (False)
    angle_reference : int
        Angle to subtract from the degree of freedom when comparing to the
        target angle
    target : int
        The +/- range the desired degree of freedom needs to be outside of to
        trigger a state change

    Methods
    -------
    __init__(dof_key)
        Initializes the dof, state, angle_reference, and target values
    checkStateATrigger
        Checks if the puck has moved to a negative angle past the target range.
    checkStateBTrigger
        Checks if the puck has moved to a positive angle past the target range.
    '''
    degrees_of_freedom = {'roll' : 0, 'pitch': 1, 'yaw': 2}

    def __init__(self, dof_key: str = 'pitch'):
        '''
        Initializes the dof, state, angle_reference, and target values

        Initializes the class attributes and selects the desired roll_pitch_yaw
        variable index based on the dof_key input parameter

        Parameters
        ----------
        dof_key : string
            Key for the degrees of freedom dictionary of indices
        '''
        # gets the index for the roll_pitch_yaw data variable
        self.dof = self.degrees_of_freedom[dof_key]

        #sets the other attributes to their default states
        self.state = False
        self.angle_reference = 0
        self.target = 15


    def checkStateATrigger(self, puck: HIDPuckDongle) -> bool:
        '''
        Checks if the puck has moved to a negative angle past the target range.

        Triggers a change to the state value if the puck's desired degree of
        freedom has moved from a positive value above the target number to a
        negative value below the negative of the target value.

        Parameters
        ----------
        puck : HIDPuckDongle object
            connection to the dongle for accessing the yellow puck's roll,
            pitch, or yaw angle

        Returns
        -------
        state : bool
            Returns if the state has switched values. True is it changed from
            False to True
        '''
        # if the state is already true, this method does not need to run
        if self.state:
            return

        # get the desired degree of freedom's angle
        pos = puck.puck_1_packet.roll_pitch_yaw[self.dof]

        # if the angle does not exist, return nothing
        if not pos:
            return

        # switch the state's value if the degree of freedom is below the
        # negative of the target
        if (pos - self.angle_reference) < -self.target:
            self.state = True

        # return the state value as if it was true, the value switched and if
        # its false, nothing changed.
        return self.state

    def checkStateBTrigger(self, puck: HIDPuckDongle) -> bool:
        '''
        Checks if the puck has moved to a positive angle past the target range.

        Triggers a change to the state value if the puck's desired degree of
        freedom has moved from a negative value below the negative of the
        target number to a positive value above the target value.

        Parameters
        ----------
        puck : HIDPuckDongle object
            connection to the dongle for accessing the yellow puck's roll,
            pitch, or yaw angle

        Returns
        -------
        bool
            Returns if the state has switched values. True is it changed from
            True to False
        '''
        # if the state is already false, this method does not need to run
        if not self.state:
            return

        # get the desired degree of freedom's angle
        pos = puck.puck_1_packet.roll_pitch_yaw[self.dof]

        # if the angle does not exist, return nothing
        if not pos:
            return

        # switch the state's value if the degree of freedom is above the the
        # target value
        if (pos - self.angle_reference) > self.target:
            self.state = False

        # return the opposite of the state value as if it was false, the value
        # switched and if its true, nothing changed.
        return not self.state
