from pr2_pick_main import handle_service_exceptions
from pr2_pick_perception import DataSaver
from pr2_pick_perception.srv import CropShelfRequest
from pr2_pick_perception.srv import SegmentItemsRequest
from geometry_msgs.msg import Point
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2
import outcomes
import rospy
import smach
from pr2_pick_manipulation.srv import MoveHead
import visualization as viz


class SenseBinExperiment(smach.State):
    """Performs sensing on a bin.
    """
    name = 'SENSE_BIN'

    def __init__(self, tts, crop_shelf, markers,move_head, **kwargs):
        """Constructor for this state.
        tts: The text-to-speech publisher.
        crop_shelf: The shelf cropping service proxy.
        """
        smach.State.__init__(
            self,
            outcomes=[outcomes.SENSE_BIN_SUCCESS, outcomes.SENSE_BIN_NO_OBJECTS,
                      outcomes.SENSE_BIN_FAILURE],
            input_keys=['bin_id', 'debug', 'current_target',
                        'current_bin_items', 're_sense_attempt', 'previous_item', 'current_trial'],
            output_keys=['clusters', 'target_cluster', 'target_descriptor',
                         'target_model', 're_grasp_attempt', 'current_target'])
        self._tts = tts
        self._tuck_arms = kwargs['tuck_arms']
        self._crop_shelf = crop_shelf
        self._segment_items = kwargs['segment_items']
        self._markers = markers
        self._get_item_descriptor = kwargs['get_item_descriptor']
        self._classify_target_item = kwargs['classify_target_item']
        self._lookup_item = kwargs['lookup_item']
        self._move_head = move_head
        self._positions = ["Position 1: Front Centre", "Position 2: Front Left", "Position 3: Front Right", "Position 4: Back"]
        self._orientations = ["Orientation 1: Facing Side", "Orientation 2: Facing Front", "Orientation 3: Angled"]

    @handle_service_exceptions(outcomes.SENSE_BIN_FAILURE)
    def execute(self, userdata):

        if 're_sense_attempt' in userdata and userdata.re_sense_attempt:
            userdata.re_grasp_attempt = True
        else:
            userdata.re_grasp_attempt = False
        self._tuck_arms.wait_for_service()
        tuck_success = self._tuck_arms(tuck_left=False, tuck_right=False)

        rospy.loginfo('Sensing bin {}'.format(userdata.bin_id))
        self._tts.publish('Sensing bin {}'.format(userdata.bin_id))
        self._move_head.wait_for_service()
        move_head_success = self._move_head(0, 0, 0, 'bin_K')
        self._lookup_item.wait_for_service()
        lookup_response = self._lookup_item(item=userdata.current_target)
        target_model = lookup_response.model
        userdata.target_model = target_model
      
        item_name = userdata.current_trial["item_name"]
        position = userdata.current_trial["position"]
        orientation = userdata.current_trial["orientation"]

        print "_______________________________"
        print "Place item: " + str(item_name)
        print "In " + str(self._positions[position])
        print "With " + str(self._orientations[orientation])
        print "_______________________________" 
        raw_input("Press enter after placing the item.")
        current_bin_items = userdata.current_target

        # Crop shelf.
        crop_request = CropShelfRequest(cellID=userdata.bin_id)
        self._crop_shelf.wait_for_service()
        crop_response = self._crop_shelf(crop_request)

        # Segment items
        segment_request = SegmentItemsRequest(cloud=crop_response.cloud, items=current_bin_items)
        self._segment_items.wait_for_service()
        segment_response = self._segment_items(segment_request)
        clusters = segment_response.clusters.clusters
        userdata.clusters = clusters
        rospy.loginfo('[SenseBin] Found {} clusters.'.format(
            len(clusters)))
        if len(clusters) == 0:
            rospy.logerr('[SenseBin]: No clusters found!')
            return outcomes.SENSE_BIN_FAILURE

        descriptors = []
        for i, cluster in enumerate(clusters):
            # Publish visualization
            points = pc2.read_points(cluster.pointcloud, skip_nans=True)
            point_list = [Point(x=x, y=y, z=z) for x, y, z, rgb in points]
            if len(point_list) == 0:
                rospy.logwarn('[SenseBin]: Cluster with 0 points returned!')
                continue
            viz.publish_cluster(self._markers, point_list,
                                'bin_{}'.format(userdata.bin_id),
                                'bin_{}_items'.format(userdata.bin_id), i)

            # Get descriptor
            self._get_item_descriptor.wait_for_service()
            response = self._get_item_descriptor(cluster=cluster)
            descriptors.append(response.descriptor)

        # Classify which cluster is the target item.
        if len(descriptors) == 0:
            rospy.logerr('[SenseBin]: No descriptors found!')
            return outcomes.SENSE_BIN_FAILURE
	"""
        self._classify_target_item.wait_for_service()
        response = self._classify_target_item(
            descriptors=descriptors,
            target_item=userdata.current_target,
            all_items=current_bin_items)
	"""
        index = 0
        userdata.target_cluster = clusters[index]
        userdata.target_descriptor = descriptors[index]
        #rospy.loginfo(
        #    'Classified cluster #{} as target item ({} confidence)'.format(
        #        index, response.confidence))
	
        if userdata.debug:
            raw_input('[SenseBin] Press enter to continue: ')
        return outcomes.SENSE_BIN_SUCCESS
