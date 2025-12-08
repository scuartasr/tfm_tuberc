#!/usr/bin/env Rscript
# fit_apc_stan.R
#
# This script reads a Lexis matrix of mortality rates by age group and period,
# transforms the data to long format, constructs an age-period-cohort (APC)
# model using Stan, and fits the model using MCMC via rstan. The model
# decomposes log mortality rates into additive age, period, and cohort
# effects with random-walk smoothing priors, and returns posterior summaries
# and example plots of the estimated effects.

library(rstan)
library(dplyr)
library(tidyr)
library(ggplot2)

## Set Stan options
options(mc.cores = parallel::detectCores())
rstan_options(auto_write = TRUE)

## Read mortality Lexis matrix
#data_path <- "../../data/processed/mortalidad/tasa_mortalidad_lexis.csv"
data_path <- "./data/processed/mortalidad/tasa_mortalidad_lexis.csv"
df <- read.csv(data_path)

## Convert from wide (age x period) to long format
# - gr_et column represents the age group index
# - other columns represent calendar years (periods)
df_long <- df %>%
  pivot_longer(
    cols = -gr_et,
    names_to = "period",
    values_to = "rate"
  ) %>%
  mutate(
    age = gr_et,
    period = as.integer(period),
    # cohort year is period minus (age - 1)
    cohort_year = period - (age - 1)
  )

## Create consecutive integer indices for age, period, and cohort
age_levels <- sort(unique(df_long$age))
period_levels <- sort(unique(df_long$period))
cohort_levels <- sort(unique(df_long$cohort_year))

df_long <- df_long %>%
  mutate(
    age_idx = match(age, age_levels),
    period_idx = match(period, period_levels),
    cohort_idx = match(cohort_year, cohort_levels),
    log_rate = log(rate + 1e-6)  # avoid log(0)
  )

## Prepare data for Stan
stan_data <- list(
  N = nrow(df_long),
  A = length(age_levels),
  P = length(period_levels),
  C = length(cohort_levels),
  age = df_long$age_idx,
  period = df_long$period_idx,
  cohort = df_long$cohort_idx,
  log_rate = df_long$log_rate
)

## Compile Stan model
stan_file <- "./modelos/R/apc_model.stan"
message("Compiling Stan model...")
apc_model <- rstan::stan_model(file = stan_file)

## Fit the model using MCMC
message("Sampling from the posterior...")
fit <- sampling(
  apc_model,
  data = stan_data,
  chains = 4,
  iter = 2000,
  warmup = 500,
  seed = 1234
)

## Summarize results
print(fit, pars = c("mu", "sigma_a", "sigma_p", "sigma_c", "sigma_y"))
print(fit, pars = c("a", "p", "c"))

## Extract posterior means of effects for plotting
posterior <- rstan::extract(fit)
age_effect <- apply(posterior$a, 2, mean)
period_effect <- apply(posterior$p, 2, mean)
cohort_effect <- apply(posterior$c, 2, mean)

age_df <- data.frame(age = age_levels, effect = age_effect)
period_df <- data.frame(period = period_levels, effect = period_effect)
cohort_df <- data.frame(cohort = cohort_levels, effect = cohort_effect)

## Plot estimated effects
p_age <- ggplot(age_df, aes(age, effect)) +
  geom_line() +
  geom_point() +
  labs(
    title = "Efecto de la Edad (media posterior)",
    x = "Grupo etario",
    y = "Efecto"
  ) +
  theme_minimal()

p_period <- ggplot(period_df, aes(period, effect)) +
  geom_line() +
  geom_point() +
  labs(
    title = "Efecto del Período (media posterior)",
    x = "Año",
    y = "Efecto"
  ) +
  theme_minimal()

p_cohort <- ggplot(cohort_df, aes(cohort, effect)) +
  geom_line() +
  geom_point() +
  labs(
    title = "Efecto de la Cohorte (media posterior)",
    x = "Año de cohorte",
    y = "Efecto"
  ) +
  theme_minimal()

## Save plots to files
ggsave("age_effect_plot.png", plot = p_age, width = 6, height = 4)
ggsave("period_effect_plot.png", plot = p_period, width = 6, height = 4)
ggsave("cohort_effect_plot.png", plot = p_cohort, width = 6, height = 4)

message("Model fitting and plotting complete. Check the generated plots: age_effect_plot.png, period_effect_plot.png, cohort_effect_plot.png.")