#!/usr/bin/env python

"""The main state machine for the picking challenge.
"""

from bin_data import BinData
import rospy
import smach
import smach_ros
import states
import state_machine_factory


def main():
    rospy.init_node('pr2_pick_state_machine')
    sm = state_machine_factory.real_robot()

    # The current bin being attempted.
    sm.userdata.current_bin = None

    # Holds data about the state of each bin.
    sm.userdata.bin_data = {}
    for bin_id in 'ABCDEFGHIJKL':
        sm.userdata.bin_data[bin_id] = BinData(id, False, False)

    try:
        sis = smach_ros.IntrospectionServer(
            'state_machine_introspection_server', sm, '/')
        sis.start()
        outcome = sm.execute()
    except:
        sis.stop()
        rospy.signal_shutdown('Exception in the state machine.')

    rospy.spin()
    sis.stop()


if __name__ == '__main__':
    main()
