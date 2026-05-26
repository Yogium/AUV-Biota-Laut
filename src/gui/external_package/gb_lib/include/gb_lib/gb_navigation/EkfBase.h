/*
 * Copyright (c) 2017 Iqua Robotics SL - All Rights Reserved
 *
 * This file is subject to the terms and conditions defined in file
 * 'LICENSE.txt', which is part of this source code package.
 */

#ifndef GB_LIB_INCLUDE_GB_LIB_GB_NAVIGATION_EKFBASE_H_
#define GB_LIB_INCLUDE_GB_LIB_GB_NAVIGATION_EKFBASE_H_

// Don't panic!!! This file is for the COLA2 project.
// However, as all the included files that it is going to need
// are currently developed in this other project, I've started
// to work with it here.

#include <Eigen/Dense>

#include <iostream>
#include <map>
#include <utility>
#include <string>
#include <vector>

#define MAX_COV 0.025

class EkfBase
{
/************
 * Protected
 * -- Only accessible from class that defines EkfBase and class that inherit EkfBase
************/

protected:
    void updatePrediction();

    unsigned int state_vector_size_;    //!< size of state vector
    double last_prediction_ = 0.0;      //!< last prediction time
    double last_correction_ = 0.0;
    double filter_updates_;             //!< number of updates already done
    Eigen::MatrixXd Q_;                 //!< State noise covariance matrix
    bool init_ekf_ = false;             //!< filter initialized
    Eigen::VectorXd x_;                 //!< state vector
    Eigen::MatrixXd P_;                 //!< covariance matrix
    // Eigen::MatrixXd _x;                 //!< old state vector x_k
    // Eigen::MatrixXd _P;                 //!< old covariance matrix P_k
    // Eigen::MatrixXd _x_;                //!< propagated state vector x_k+1
    // Eigen::MatrixXd _P_;                //!< propagated covariance matrix P_k+1


/************
 * Private 
 * -- Only accessible from class that defines EkfBase
************/
private:
    /**
    * \brief Compute linearized state transition matrix
    *   Equations are:
    *       Fk = df(x,w)/dx
    *       A = exp(F * Ts) , where Ts is sampling period
    *   Using Taylor's expansion on A,
    *       A = (I + Fk * Ts)
    * 
    * \param t Timestamp
    * \return state transition matrix
    */
    virtual Eigen::MatrixXd computeA(const double t) const = 0;

    /**
    * \brief Compute system noise distribution matrix
    *  
    * 
    * \param t Timestamp
    * \return system noise distribution matrix G
    */
    virtual Eigen::MatrixXd computeG() const = 0;

    virtual Eigen::MatrixXd computeF() const = 0;

public:
    /**
    * \brief Constructor.
    *
    * \param state_vector_size Size in rows of the state vector
    * \param now Current time
    */
    EkfBase(const unsigned int state_vector_size, const Eigen::VectorXd q_var, const double now);

    /**
    * \brief Initializing EKF
    *
    * \param state Error state in EKF
    * \param p_var Error state covariance Matrix P
    */
    void initEkf(const Eigen::VectorXd state, const Eigen::VectorXd p_var);

    /**
    * \brief State propagation
    * 
    * The prediction equations are:
    *   x = f(x)
    *   P = A P AT + G Q GT
    *   where:
    *     A = linearized state transition matrix 
    *     G = system noise distribution matrix
    *
    * \param now Current time
    * \return True if period is valid
    */
    bool makePrediction(const double now);

    /**
    * \brief Measurement update
    *
    * \param z Measurement innovation vector
    * \param R Measurement noise
    * \param H Linearized measurement matrix
    * \param V Not used yet 
    * \param mahalobis_distance_threshold asdasd
    */
    bool applyUpdate(const Eigen::VectorXd z, const Eigen::MatrixXd R, 
                     const Eigen::MatrixXd H, const Eigen::MatrixXd V,
                     const double mahalanobis_distance_threshold);
    /**
    * \brief Print state vector x and covariance matrix onscreen.
    */
    void showStateVector();

    /**
    * \brief Get state vector x.
    *
    * \return State vector.
    */
    Eigen::VectorXd getStateVector();

    /**
    * \brief Get state vector x.
    *
    * \return State vector.
    */
    Eigen::VectorXd resetStateVector();

    /**
    * \brief Get covariance matrix P
    *
    * \return State covariance matrix P
    */
    Eigen::MatrixXd getCovarianceMatrix();

    double mahalanobisDistance(const Eigen::VectorXd& innovation, const Eigen::MatrixXd& R,
                                        const Eigen::MatrixXd& H, const Eigen::MatrixXd& V);

    void checkIntegrity();

};

#endif