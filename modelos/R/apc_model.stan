data {
  int<lower=1> N;       // number of observations
  int<lower=1> A;       // number of age groups
  int<lower=1> P;       // number of periods
  int<lower=1> C;       // number of cohorts
  int<lower=1> age[N];     // age index for each observation
  int<lower=1> period[N];  // period index for each observation
  int<lower=1> cohort[N];  // cohort index for each observation
  vector[N] log_rate;      // observed log mortality rates
}

parameters {
  vector[A] a_raw;         // raw age effects before centering
  vector[P] p_raw;         // raw period effects before centering
  vector[C] c_raw;         // raw cohort effects before centering
  real mu;                 // overall intercept
  real<lower=0> sigma_a;   // SD of age random walk increments
  real<lower=0> sigma_p;   // SD of period random walk increments
  real<lower=0> sigma_c;   // SD of cohort random walk increments
  real<lower=0> sigma_y;   // observation noise (log-rate scale)
}

transformed parameters {
  vector[A] a;
  vector[P] p;
  vector[C] c;

  // impose sum-to-zero constraints on the random effects
  a = a_raw - mean(a_raw);
  p = p_raw - mean(p_raw);
  c = c_raw - mean(c_raw);
}

model {
  // smoothness priors: random-walk on age, period, and cohort
  for (i in 2:A)
    a_raw[i] - a_raw[i - 1] ~ normal(0, sigma_a);
  for (j in 2:P)
    p_raw[j] - p_raw[j - 1] ~ normal(0, sigma_p);
  for (k in 2:C)
    c_raw[k] - c_raw[k - 1] ~ normal(0, sigma_c);

  // hyperpriors
  mu ~ normal(0, 10);
  sigma_a ~ normal(0, 5);
  sigma_p ~ normal(0, 5);
  sigma_c ~ normal(0, 5);
  sigma_y ~ normal(0, 5);

  // likelihood: log_rate is observed log mortality rate
  for (n in 1:N)
    log_rate[n] ~ normal(mu + a[age[n]] + p[period[n]] + c[cohort[n]], sigma_y);
}

generated quantities {
  vector[N] log_rate_pred;
  // generate posterior predictive draws of log rates
  for (n in 1:N) {
    log_rate_pred[n] = normal_rng(mu + a[age[n]] + p[period[n]] + c[cohort[n]], sigma_y);
  }
}