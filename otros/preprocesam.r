# Lectura de los datos asociados a los fallecimientos =========================

rm(list = ls())

# Paquetes importantes ========================================================

library(tidyverse)
library(magrittr)
library(janitor)
library(readxl)

# Datos totales ===============================================================

tuberculosis_a <- data.frame()
tuberculosis_b <- data.frame()
tuberculosis_c <- data.frame()

tuberculosis <- data.frame()

# Datos de mortalidad =========================================================

# Direcciones de las bases de datos
direc1 <- paste('./Datos/Crudos/Defun', c(1979:1997), 
                '.txt', sep = '')
direc2 <- paste('./Datos/Crudos/Defun', c(2008:2011, 2014:2019), 
                '.csv', sep = '')

## Años 1979 a 1997 ===================

direc1 <- paste('./Datos/Crudos/Defun', c(1979:1997), 
                '.txt', sep = '')

# Unificación de los datos

for (elemento in direc1) {
  # Verificación del tipo de archivo
  datos <- read.csv(elemento, sep = '\t', encoding = 'utf-8', quote = "")
  datos %<>% clean_names()
  datos %<>% filter(cau_homol == 2)
  datos %<>% select(ano, sexo, gru_ed1, cod_dpto)
  tuberculosis_a <- rbind(tuberculosis_a, datos)
}

# Columna para los grupos etarios corregidos

tuberculosis_a %<>% add_column(gr_et = NA)

# Grupos etarios corregidos

tuberculosis_a <- within(tuberculosis_a, 
                         gr_et[gru_ed1 < 8] <- 1)
tuberculosis_a <- within(tuberculosis_a, 
                         gr_et[gru_ed1 > 7 & gru_ed1 < 23] <- gru_ed1[gru_ed1 > 7 & gru_ed1 < 23] - 6)
tuberculosis_a <- within(tuberculosis_a, 
                         gr_et[gru_ed1 > 22 & gru_ed1 != 25] <- 17)

tuberculosis_a %<>% na.omit()

## Años 1998 a 2007 ===================

direc2 <- paste('./Datos/Crudos/Defun', 1998:2007, 
                '.txt', sep = '')

# Unificación de los datos

for (elemento in direc2) {
  # Verificación del tipo de archivo
  datos <- read.csv(elemento, sep = '\t', encoding = 'utf-8', quote = "")
  datos %<>% clean_names()
  datos %<>% filter(cau_homol == 2)
  datos %<>% select(ano, sexo, gru_ed1, cod_dpto)
  tuberculosis_b <- rbind(tuberculosis_b, datos)
}

# Columna para los grupos etarios corregidos

tuberculosis_b %<>% add_column(gr_et = NA)

# Grupos etarios corregidos

tuberculosis_b <- within(tuberculosis_b, 
                         gr_et[gru_ed1 < 9] <- 1)
tuberculosis_b <- within(tuberculosis_b, 
                         gr_et[gru_ed1 > 8 & gru_ed1 < 24] <- gru_ed1[gru_ed1 > 8 & gru_ed1 < 24] - 7)
tuberculosis_b <- within(tuberculosis_b, 
                         gr_et[gru_ed1 > 23 & gru_ed1 != 26] <- 17)

tuberculosis_b %<>% na.omit()

## Años 2008 a 2020 ===================

direc3a <- paste('./Datos/Crudos/Defun', c(2008:2011, 2014:2019), 
                '.csv', sep = '')
direc3b <- paste('./Datos/Crudos/Defun', 2012:2013, 
                '.txt', sep = '')
direc3 <- c(direc3a, direc3b)


for (elemento in direc3) {
  # Verificación del tipo de archivo
  if (elemento %>% endsWith('txt')) {
    datos <- read.csv(elemento, sep = '\t', encoding = 'utf-8', quote = "")
  }
  else {
    datos <- read.csv(elemento, sep = ',', encoding = 'utf-8', quote = "")
  }
  datos %<>% clean_names()
  datos %<>% filter(cau_homol == 2)
  datos %<>% select(ano, sexo, gru_ed1, cod_dpto)
  tuberculosis_c <- rbind(tuberculosis_c, datos)
}

# Columna para los grupos etarios corregidos

tuberculosis_c %<>% add_column(gr_et = NA)

# Grupos etarios corregidos

tuberculosis_c <- within(tuberculosis_c, 
                         gr_et[gru_ed1 < 9] <- 1)
tuberculosis_c <- within(tuberculosis_c, 
                         gr_et[gru_ed1 > 8 & gru_ed1 < 24] <- gru_ed1[gru_ed1 > 8 & gru_ed1 < 24] - 7)
tuberculosis_c <- within(tuberculosis_c, 
                         gr_et[gru_ed1 > 23 & gru_ed1 != 29] <- 17)

tuberculosis_c %<>% na.omit()

## Unificación ========================

tuberculosis <- rbind(tuberculosis_a, tuberculosis_b, tuberculosis_c)

tuberculosis %<>% select(-c(gru_ed1))

tuberculosis$cod_dpto %>% table

# Regiones ====================================================================

direc_reg <- './Datos/Otros/cods_dptos_colombia.txt'

regiones <- read.csv(direc_reg, sep = '\t', encoding = 'latin1', quote = '')

regiones$cod_dpto %>% sort

# Incorporación de las regiones

tuberculosis <- left_join(x = tuberculosis, y = regiones,
                 by = 'cod_dpto')

tuberculosis %<>%
  na.omit() %>% 
  select(ano, sexo, gr_et, region)

# Guardado ====================================================================

write.csv(tuberculosis, './Datos/Trabajo/tuberculosis_raw.txt',
          row.names = TRUE)

# Sumarización ================================================================

sum_tub <- tuberculosis %>% 
  group_by(ano, sexo, gr_et, region) %>% 
  summarise(cases = n())
write.csv(sum_tub, './Datos/Trabajo/tuber_agrup.txt', row.names = TRUE)