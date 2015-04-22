from bin_data import BinData
import outcomes
import rospy
import smach


class UpdatePlan(smach.State):
    """Decides on the next item to pick.

    Its preference is to go from bottom to top, then from left to right.
    It prefers trying bins that haven't been attempted before. If all the bins
    have been attempted, then it will try going to bins for which the attempt
    failed. It will do this until there are no more items to pick.
    """
    name = 'UPDATE_PLAN'

    def __init__(self, **kwargs):
        """Constructor for this state.

        Args:
          tts: The text to speech publisher.
        """
        smach.State.__init__(
            self,
            outcomes=[
                outcomes.UPDATE_PLAN_NEXT_OBJECT,
                outcomes.UPDATE_PLAN_NO_MORE_OBJECTS,
                outcomes.UPDATE_PLAN_FAILURE
            ],
            input_keys=['bin_data'],
            output_keys=['output_bin_data', 'next_bin']
        )
        self._tts = kwargs['tts']
        self._get_items = kwargs['get_items']
        self._set_items = kwargs['set_items']
        self._get_target_items = kwargs['get_target_items']
        self._preferred_order = 'JKLGHIDEFABC'

    def execute(self, userdata):
        rospy.loginfo('Updating plan.')
        self._tts.publish('Updating plan.')


        '''
        Planning comment:
        We want to know if the bin we want to acess has any items we want.
        Obviously, we don't want to go to bins where there is nothing we want

        Sudo-code picking:

        foreach bin
            if bin has not been visited and has useful item in it
                chose that bin

        foreach bin
            if bin has not had sucess and has useful item in it
                chose that bin

        If we get here there are no bins worth going to
        '''


        for bin_id in self._preferred_order:
            if not userdata.bin_data[bin_id].visited and len(self.get_target_items(bin_id)) > 0:
                userdata.next_bin = bin_id
                bin_data = userdata.bin_data.copy()
                bin_data[bin_id] = bin_data[bin_id]._replace(visited=True)
                userdata.output_bin_data = bin_data
                return outcomes.UPDATE_PLAN_NEXT_OBJECT

        for bin_id in self._preferred_order:
            if not userdata.bin_data[bin_id].succeeded and len(self.get_target_items(bin_id)) > 0:
                userdata.next_bin = bin_id
                return outcomes.UPDATE_PLAN_NEXT_OBJECT

        return outcomes.UPDATE_PLAN_NO_MORE_OBJECTS
