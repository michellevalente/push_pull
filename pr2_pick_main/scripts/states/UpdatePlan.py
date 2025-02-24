from bin_data import BinData
from pr2_pick_contest import PickingStrategy
from pr2_pick_main import handle_service_exceptions
import outcomes
import rospy
import smach
from pr2_pick_main.web_interface import WebInterface
from PushPullActions import RepositionAction
import rospkg
import json
import copy


class UpdatePlan(smach.State):
    name = 'UPDATE_PLAN'

    def __init__(self, **services):
        """Constructor for this state.
        """
        smach.State.__init__(
            self,
            outcomes=[
                outcomes.UPDATE_PLAN_NEXT_OBJECT,
                outcomes.UPDATE_PLAN_FAILURE
            ],
            input_keys=['debug', 'current_trial_num'],
            output_keys=['current_trial', 'current_trial_num']
        )
	
        self._tts = services['tts']
        self._interface = WebInterface()

        rospack = rospkg.RosPack()
        params_file = str(rospack.get_path('pr2_pick_contest')) + '/config/experiment_params.json' 

        with open(params_file) as data_file:    
            self._experiment_params = json.load(data_file)
        self._trials = self.generate_trials()
        self._total_trials = len(self._trials)

    def generate_trials(self):
        trials = []
        actions = RepositionAction.get_all_actions()

        for item in self._experiment_params["items"]:
            for position in item["positions"]:
                for orientation in item["orientations"]:
                    for action in item["actions"]:
                        trial = {}
                        trial["position"] = position
                        trial["orientation"] = orientation
                        trial["action"] = action
                        trial["item_name"] = item["item_name"]
                        trials.append(copy.copy(trial))
        return trials  

    @handle_service_exceptions(outcomes.UPDATE_PLAN_FAILURE)
    def execute(self, userdata):

        next_trial_num = userdata.current_trial_num + 1
        userdata.current_trial_num = next_trial_num
        rospy.loginfo('Trial number ' + str(next_trial_num) + ' out of ' + str(self._total_trials))
        userdata.current_trial = self._trials[next_trial_num]
        return outcomes.UPDATE_PLAN_NEXT_OBJECT

