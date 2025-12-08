#!/usr/bin/env Rscript
# fit_apc_stan_mod.R
#
# Versión modificada del script de ajuste APC con Stan.
# Reduce el número de iteraciones y cadenas para acelerar el muestreo,
# imprime mensajes intermedios y utiliza `refresh` para mostrar el progreso.

library(rstan)
library(dplyr)
library(tidyr)
library(ggplot2)

## Configuración de Stan
options(mc.cores = parallel::detectCores())
rstan_options(auto_write = TRUE)

## Rutas de los archivos
data_path <- "./data/processed/mortalidad/tasa_mortalidad_lexis.csv"
stan_file <- "./modelos/R/apc_model.stan"

## Leer datos
df <- read.csv(data_path)
cat("Datos cargados, dimensiones:", dim(df), "\n")

## Reorganizar a formato largo
df_long <- df %>%
  pivot_longer(
    cols = -gr_et,
    names_to = "period",
    values_to = "rate"
  ) %>%
  mutate(
    age = gr_et,
    period = as.integer(period),
    cohort_year = period - (age - 1)
  )

age_levels <- sort(unique(df_long$age))
period_levels <- sort(unique(df_long$period))
cohort_levels <- sort(unique(df_long$cohort_year))

df_long <- df_long %>%
  mutate(
    age_idx = match(age, age_levels),
    period_idx = match(period, period_levels),
    cohort_idx = match(cohort_year, cohort_levels),
    log_rate = log(rate + 1e-6)
  )

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

cat("Datos listos para Stan. Compilando modelo...\n")
apc_model <- rstan::stan_model(file = stan_file)
cat("Modelo compilado. Iniciando muestreo...\n")

## Ajustar el modelo (menos iteraciones y cadenas, y con refresco de progreso)
fit <- sampling(
  apc_model,
  data = stan_data,
  chains = 2,
  iter = 1000,
  warmup = 500,
  seed = 1234,
  refresh = 100 # muestra progreso cada 100 iteraciones
)

cat("Muestreo completado. Resumen del ajuste:\n")
print(fit, pars = c("mu", "sigma_a", "sigma_p", "sigma_c", "sigma_y"))

## Extraer medias posteriores de los efectos
posterior <- rstan::extract(fit)

##
## Obtenemos las medias posteriores de los efectos de edad, periodo y cohorte.
## En algunos casos, rstan no devuelve las variables definidas en
## `transformed parameters` directamente (como a, p, c). Para evitar el
## error "dim(X) must have a positive length", comprobamos si existen
## estas variables. Si no existen, calculamos los efectos a partir de
## los parámetros originales (a_raw, p_raw, c_raw) centrándolos por
## iteración.

if (!("a" %in% names(posterior))) {
  # Calcular los efectos centrados manualmente.
  cat("Las variables 'a', 'p' y 'c' no están en posterior; se calcularán a partir de a_raw, p_raw y c_raw.\n")
  # Efecto de edad
  a_raw_mat <- posterior$a_raw  # dimensiones: iteraciones x A
  # media por iteración
  row_means_a <- rowMeans(a_raw_mat)
  # media por columna (por grupo etario)
  col_means_a <- colMeans(a_raw_mat)
  # media de la media por iteración
  mean_row_means_a <- mean(row_means_a)
  age_effect <- col_means_a - mean_row_means_a
  # Efecto de periodo
  p_raw_mat <- posterior$p_raw
  row_means_p <- rowMeans(p_raw_mat)
  col_means_p <- colMeans(p_raw_mat)
  mean_row_means_p <- mean(row_means_p)
  period_effect <- col_means_p - mean_row_means_p
  # Efecto de cohorte
  c_raw_mat <- posterior$c_raw
  row_means_c <- rowMeans(c_raw_mat)
  col_means_c <- colMeans(c_raw_mat)
  mean_row_means_c <- mean(row_means_c)
  cohort_effect <- col_means_c - mean_row_means_c
} else {
  # si se guardaron las variables transformadas, usamos extract directamente
  age_effect <- apply(posterior$a, 2, mean)
  period_effect <- apply(posterior$p, 2, mean)
  cohort_effect <- apply(posterior$c, 2, mean)
}

age_df <- data.frame(age = age_levels, effect = age_effect)
period_df <- data.frame(period = period_levels, effect = period_effect)
cohort_df <- data.frame(cohort = cohort_levels, effect = cohort_effect)

## Graficar efectos
p_age <- ggplot(age_df, aes(age, effect)) +
  geom_line() +
  geom_point() +
  labs(title = "Efecto de la Edad (media posterior)", x = "Grupo etario", y = "Efecto") +
  theme_minimal()

p_period <- ggplot(period_df, aes(period, effect)) +
  geom_line() +
  geom_point() +
  labs(title = "Efecto del Período (media posterior)", x = "Año", y = "Efecto") +
  theme_minimal()

p_cohort <- ggplot(cohort_df, aes(cohort, effect)) +
  geom_line() +
  geom_point() +
  labs(title = "Efecto de la Cohorte (media posterior)", x = "Año de cohorte", y = "Efecto") +
  theme_minimal()

ggsave("age_effect_plot_mod.png", plot = p_age, width = 6, height = 4)
ggsave("period_effect_plot_mod.png", plot = p_period, width = 6, height = 4)
ggsave("cohort_effect_plot_mod.png", plot = p_cohort, width = 6, height = 4)

cat("Script completado. Revisa los gráficos generados y el resumen del modelo.\n")