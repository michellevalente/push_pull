#!/usr/bin/env python

"""The main state machine for the picking challenge.
"""

from bin_data import BinData
import argparse
import rospy
import smach
import smach_ros
import state_machine_factory
import states


def main(mock=False, test_move_to_bin=False, test_drop_off_item=False, debug=False):
    rospy.init_node('pr2_pick_state_machine')
    sm = None
    if mock:
        sm = state_machine_factory.mock_robot()
    elif test_move_to_bin:
        sm = state_machine_factory.test_move_to_bin()
    elif test_drop_off_item:
        sm = state_machine_factory.test_drop_off_item()
    else:
        sm = state_machine_factory.real_robot()

    # Whether to step through checkpoints.
    sm.userdata.debug = debug

    # The current bin being attempted.
    sm.userdata.current_bin = None

    # Holds data about the state of each bin.
    sm.userdata.bin_data = {}
    for bin_id in 'ABCDEFGHIJKL':
        sm.userdata.bin_data[bin_id] = BinData(id, False, False)

    # A list of clusters (pr2_pick_perception/Cluster.msg) for objects in the
    # current bin.
    sm.userdata.clusters = []

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
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--mock', action='store_true',
        help=('True if you want to create a state machine with mock robot'
            ' components.')
    )
    group.add_argument(
        '--test_move_to_bin', action='store_true',
        help=('True to create a minimal state machine for testing the'
              'MoveToBin state.')
    )
    group.add_argument(
        '--test_drop_off_item', action='store_true',
        help=('True to create a minimal state machine for testing the'
              'DropOffItem state.')
    )
    parser.add_argument(
        '--debug', action='store_true',
        help=('True if you want to step through debugging checkpoints.')
    )
    args = parser.parse_args(args=rospy.myargv()[1:])
    sim_time = rospy.get_param('use_sim_time', False)
    if sim_time != False:
        rospy.logwarn('Warning: use_sim_time was set to true. Setting back to '
            'false. Verify your launch files.')
        rospy.set_param('use_sim_time', False)
    main(args.mock, args.test_move_to_bin, args.test_drop_off_item, args.debug)
