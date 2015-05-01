#include "pr2_pick_perception/pcl.h"

#include "geometry_msgs/Point.h"
#include "geometry_msgs/TransformStamped.h"
#include "pcl/common/pca.h"
#include "pcl/filters/filter.h"
#include "pcl/point_types.h"
#include "pcl_conversions/pcl_conversions.h"
#include "ros/ros.h"
#include "sensor_msgs/PointCloud2.h"
#include <Eigen/Dense>
#include <tf/transform_listener.h>

#include <algorithm>
#include <math.h>
#include <vector>

namespace pr2_pick_perception {
void PlanarPrincipalComponents(const pcl::PointCloud<pcl::PointXYZRGB>& cloud,
                               geometry_msgs::Quaternion* component1,
                               geometry_msgs::Quaternion* component2,
                               double* value1, double* value2) {
  pcl::PointCloud<pcl::PointXYZRGB> projected(cloud);

  // Project points onto XY plane.
  float center_x = 0;
  float center_y = 0;
  for (size_t i = 0; i < projected.points.size(); ++i) {
    pcl::PointXYZRGB& point = projected[i];
    point.z = 0;
    center_x += point.x;
    center_y += point.y;
  }
  center_x /= projected.points.size();
  center_y /= projected.points.size();
  for (size_t i = 0; i < projected.points.size(); ++i) {
    pcl::PointXYZRGB& point = projected[i];
    point.x -= center_x;
    point.y -= center_y;
  }
  pcl::PCA<pcl::PointXYZRGB> pca(true);
  pca.setInputCloud(projected.makeShared());

  // Return eigenvalues.
  Eigen::Vector3f values = pca.getEigenValues();
  *value1 = values(0);
  *value2 = values(1);

  // Return eigenvectors.
  Eigen::Matrix3f vectors = pca.getEigenVectors();
  double theta0 = atan2(vectors(1, 0), vectors(0, 0));
  double theta1 = atan2(vectors(1, 1), vectors(0, 1));

  Eigen::Quaternion<double> q1;
  q1 = Eigen::AngleAxis<double>(theta0, Eigen::Vector3d::UnitZ());
  component1->w = q1.w();
  component1->x = q1.x();
  component1->y = q1.y();
  component1->z = q1.z();

  Eigen::Quaternion<double> q2;
  q2 = Eigen::AngleAxis<double>(theta1, Eigen::Vector3d::UnitZ());
  component2->w = q2.w();
  component2->x = q2.x();
  component2->y = q2.y();
  component2->z = q2.z();
}

void BoundingBox(const sensor_msgs::PointCloud2& cloud,
                 geometry_msgs::TransformStamped* transform,
                 geometry_msgs::Point* bbox) {
  // Get principal components
  // geometry_msgs::Quaternion component1, component2;
  // double value1, value2;
  // PlanarPrincipalComponents(cloud, &component1, &component2, &value1,
  // &value2);

  // Build a provisional frame. Axes in the right orientation, but we don't know
  // the origin yet. Use centroid.
  // tf::Transform provisional_frame = tf::Transform(orientation, origin);

  // for each point:
  //   transform it into the provisional frame
  //   cumulatively track greatest and smallest x, y, z

  // Build the item frame
  // origin at smallest x, y, z
  // orientation same as provisional frame

  // construct the bbox point
  // largest - smallest x, y, z
}

void ComputeColorHistogram(const pcl::PointCloud<pcl::PointXYZRGB>& cloud,
                           const int num_bins, std::vector<int>* histogram) {
  double bin_size = 255.0 / num_bins;
  histogram->clear();
  histogram->resize(3 * num_bins);
  for (size_t i = 0; i < histogram->size(); ++i) {
    (*histogram)[i] = 0;
  }

  for (size_t i = 0; i < cloud.size(); ++i) {
    const pcl::PointXYZRGB& point = cloud[i];
    uint8_t red = point.r;
    uint8_t green = point.g;
    uint8_t blue = point.b;

    int red_bin =
        std::min(static_cast<int>(floor(red / bin_size)), num_bins - 1);
    int green_bin =
        std::min(static_cast<int>(floor(green / bin_size)), num_bins - 1);
    int blue_bin =
        std::min(static_cast<int>(floor(blue / bin_size)), num_bins - 1);
    (*histogram)[red_bin] += 1;
    (*histogram)[num_bins + green_bin] += 1;
    (*histogram)[num_bins + num_bins + blue_bin] += 1;
  }
}

}  // namespace pr2_pick_perception
