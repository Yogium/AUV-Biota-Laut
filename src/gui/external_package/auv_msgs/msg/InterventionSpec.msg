# Specification of an intervention operation, containing one or more
# intervention tasks.

# TODO: View is an image mosaic of several raw images.
# Where is this view stored?
string view_image_id

ImageFeature[] view_feature

# Bounding box of the Target of Interest inside the view.
sensor_msgs/RegionOfInterest roi
float32 roi_rotation

ImageFeature[] object_feature

# Array of task specifications. All tasks must be completed for intervention
# to succeed.
InterventionTaskSpec[] task_spec
