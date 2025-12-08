

# ==============================================================================================
# Instalar paquetes necesarios (se ejecuta después de validar la ruta)
req <- c("StMoMo", "demography", "ggplot2", "dplyr", "tidyr", "readr", "matrixStats", "here")
inst <- req[!req %in% installed.packages()]
if (length(inst) > 0) {
  install.packages(inst, repos = "https://cloud.r-project.org")
}

# Cargar librerías
library(StMoMo)
library(demography)
library(ggplot2)
library(dplyr)
library(tidyr)
library(readr)
library(matrixStats)

# ==============================================================================================
ruta <- here::here("data", "processed", "mortalidad", "tasa_mortalidad_lexis.csv")


# Leer datos
raw <- read.csv(ruta, check.names = FALSE, stringsAsFactors = FALSE)

# Años
anos <- as.integer(colnames(raw)[-1])
paste(anos)