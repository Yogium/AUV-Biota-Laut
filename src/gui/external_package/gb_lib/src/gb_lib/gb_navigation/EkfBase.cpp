#include "gb_lib/gb_navigation/EkfBase.h"
#include <ctime>

EkfBase::EkfBase(const unsigned int state_vector_size, const Eigen::VectorXd q_var, const double now ):
  state_vector_size_(state_vector_size),
  init_ekf_(false),
  filter_updates_(0)
{
    last_prediction_ = 0;
    x_.resize(state_vector_size_, 1);
    x_ = Eigen::VectorXd::Zero(state_vector_size_);
    P_.resize(state_vector_size_, state_vector_size_);
    P_ = Eigen::MatrixXd::Identity(state_vector_size_, state_vector_size_);
    Q_.resize(q_var.size(), q_var.size());
    Q_ = Eigen::ArrayXXd::Zero(q_var.size(), q_var.size());
    for (unsigned int i = 0; i < q_var.size(); ++i)
    {
        Q_(i, i) = q_var(i);
    }
}

void EkfBase::initEkf(const Eigen::VectorXd state, const Eigen::VectorXd p_var)
{
  assert(state.size() == state_vector_size_);
  assert(p_var.size() == state_vector_size_);

  for (unsigned int i = 0; i < state_vector_size_; ++i)
  {
    x_(i) = state(i);
    P_(i, i) = p_var(i);
  }

  //std::cout << "tes \n";
  //showStateVector();

  filter_updates_ = 0;
  init_ekf_ = true;
}

bool EkfBase::makePrediction(const double now)
{
  if (init_ekf_)
  {
    double period = 0.05; // musti dicek ini periodnya bener atau nggak
    // std::cout << "last_prediction: " << last_prediction_ << "\n";
    // std::cout << "now: " << now << "\n";

    //std::cout << "u:\n" << u << "\n";
    // std::cout << "period: " << period << "\n";

    if (period > 0.0 && period <= 0.25)
    {
      period = period;
      time_t t1 = clock();
      Eigen::MatrixXd F = computeF();
      // std::cout << "\nA:\n " << A << "\n";

      Eigen::MatrixXd G = computeG();

      Eigen::MatrixXd M = Eigen::MatrixXd::Zero(30,30);
      
      M.topLeftCorner(15,15) = -F;
      M.topRightCorner(15,15) = G * Q_ * G.transpose();
      M.bottomRightCorner(15,15) = F.transpose();

      Eigen::MatrixXd ExpM = Eigen::MatrixXd::Identity(30,30) + M * period;

      Eigen::MatrixXd Phi = ExpM.bottomRightCorner(15,15).transpose();

      Eigen::MatrixXd Qd = Phi * ExpM.topRightCorner(15,15);

      // std::cout << "\nPhi:\n " << Phi << "\n";

      // x_ = Phi * x_ ; //f(_x, period, A, u);
      x_ = x_ ; //f(_x, period, A, u);
      // std::cout << "\nx_:-------------------------------------------------\n " 
      // << x_.transpose() << "\n";

      P_ = Phi * P_ * Phi.transpose() + Qd;
      // P_ = F * P_ * F.transpose() + G*Q_*G.tranpose()*period;
      // checkIntegrity();
      std::cout << "\nP_:------------------Prediksi-------------------------------\n " ;
      // << P_ << "\n";

      last_prediction_ = now;

      time_t t2 = clock();
      // std::cout << P_ << "\n";
      // std::cout << "Propagation time elapsed: " << (double)(t2 - t1) / (double) CLOCKS_PER_SEC << std::endl;

      return true;
    }
    else if (period > -0.15 && period <= 0.0)
    {
      // state is the same
      x_ = x_;
      P_ = P_;
      return true;
    }
    else
    {
      std::cerr << "makePrediction invalid period " << period << "\n";
      last_prediction_ = now;  // Update time, otherwise everything will fail!
      return false;
    }
  }
  else
  {
    last_prediction_ = now;  // Update time, otherwise everything will fail!
    return false;
  }
}

bool EkfBase::applyUpdate(const Eigen::VectorXd z, const Eigen::MatrixXd R, 
                          const Eigen::MatrixXd H, const Eigen::MatrixXd V,
                          const double mahalanobis_distance_threshold)
{
  Eigen::VectorXd residual = z ; //- H *_x_;

  // const bool sanity_check = (sanity_check_value.array() < 0.0).any();
  // No threshold or distance below threshold
  // const bool mahalanobis_ok = (mahalanobis_distance_threshold < 0.0) || (distance < mahalanobis_distance_threshold);
  if (true) // || mahalanobis_ok)
  {
    time_t t1 = clock();
    // Eigen::VectorXd innovation = z ; //- H *_x_;
    //std::cout << "_x_" << _x_ << "\n";
    //std::cout << "innovation:\n" << z << "\n";
    
    // Compute updated state vector
    Eigen::MatrixXd S = H * P_ * H.transpose() + V * R * V.transpose();
    // std::cout << "S:\n" << S << "\n";
    
    Eigen::MatrixXd K = P_ * H.transpose()* S.inverse();

    std::cout << "H:\n" << H << "\n";
    std::cout << "K:\n" << K.transpose() << "\n";

    x_ = K*(residual) ;//_x_ + K*innovation;
    // std::cout << "new error_state:\n" << x_ << "\n\n";
    // std::cout << "perbaikan:\n" << K*innovation << "\n\n";

    // Compute updated covariance matrix
    unsigned int I_size = x_.size();
    Eigen::MatrixXd IKH = Eigen::MatrixXd::Identity(I_size, I_size) - K * H;
    P_ = IKH * P_ * IKH.transpose() + K*R*K.transpose();
    // P_ = IKH * P_;
    std::cout << "\n_P: --------------------Koreksi-------------\n " ;
    // << P_ << "\n";
    ++filter_updates_;
    // std::cout <<  "Filter updates : " << filter_updates_ << std::endl;
    
    time_t t2 = clock();
    std::cout << "Time elapsed: " << (double)(t2 - t1) / (double) CLOCKS_PER_SEC << std::endl;
    // checkIntegrity();

    return true;
  }
  else
  {
    std::cout << "Measurement is not valid\n";
    return false;
  }
}


void EkfBase::showStateVector()
{
  std::cout << "state Vector:\n" << x_ << "\n\n";
  std::cout << "P:\n" << P_ << "\n\n";
}

Eigen::VectorXd EkfBase::resetStateVector()
{
  Eigen::MatrixXd x ;
  x = x_ ;
  x_ = Eigen::MatrixXd::Zero(state_vector_size_, 1);
  return x;
}

Eigen::VectorXd EkfBase::getStateVector()
{
  return x_;
}

Eigen::MatrixXd EkfBase::getCovarianceMatrix()
{
  return P_;
}

double EkfBase::mahalanobisDistance(const Eigen::VectorXd& innovation, const Eigen::MatrixXd& R,
                                    const Eigen::MatrixXd& H, const Eigen::MatrixXd& V)
{
  const Eigen::MatrixXd S = H * P_ * H.transpose() + V * R * V.transpose();
  const Eigen::VectorXd d = innovation.transpose() * S.inverse() * innovation;
  return std::sqrt(d(0, 0));
}

void EkfBase::checkIntegrity()
{
  // NaN check
  for (unsigned int i = 0; i < state_vector_size_; i++)
  {
    if (std::isnan(x_(i)))
    {
      std::cout << "\033[1;31m"
                << "NaNs detected!!!"
                << "\033[0m\n";
    }
    if (P_(i, i) < 0.0)
    {
      // P_(i, i) = 1e-8;
      std::cout << "Negative values in P(" << i << "," << i << ")\n";
    }
  }
}