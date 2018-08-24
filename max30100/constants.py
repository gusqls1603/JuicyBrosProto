#!/usr/bin/env python


MAX30100_I2C_ADDRESS = 0x57

# Interrupt status register (RO)
MAX30100_REG_INTERRUPT_STATUS       = 0x00
MAX30100_IS_PWR_RDY                 = (1 << 0)
MAX30100_IS_SPO2_RDY                = (1 << 4)
MAX30100_IS_HR_RDY                  = (1 << 5)
MAX30100_IS_TEMP_RDY                = (1 << 6)
MAX30100_IS_A_FULL                  = (1 << 7)

# Interrupt enable register
MAX30100_REG_INTERRUPT_ENABLE       = 0x01
MAX30100_IE_ENB_SPO2_RDY            = (1 << 4)
MAX30100_IE_ENB_HR_RDY              = (1 << 5)
MAX30100_IE_ENB_TEMP_RDY            = (1 << 6)
MAX30100_IE_ENB_A_FULL              = (1 << 7)

# FIFO control and data registers
MAX30100_REG_FIFO_WRITE_POINTER     = 0x02
MAX30100_REG_FIFO_OVERFLOW_COUNTER  = 0x03
MAX30100_REG_FIFO_READ_POINTER      = 0x04
MAX30100_REG_FIFO_DATA              = 0x05

# Mode Configuration register
MAX30100_REG_MODE_CONFIGURATION     = 0x06
MAX30100_MC_TEMP_EN                 = (1 << 3)
MAX30100_MC_RESET                   = (1 << 6)
MAX30100_MC_SHDN                    = (1 << 7)

# SPO2 Configuration Registers
MAX30100_REG_SPO2_CONFIGURATION     = 0x07
MAX30100_SPO2_HI_RES_EN             = (1 << 6)

# Modes
MAX30100_MODE_HRONLY                = 0x02
MAX30100_MODE_SPO2_HR               = 0x03

# Sample Rates
MAX30100_SAMPRATE_50HZ              = 0x00
MAX30100_SAMPRATE_100HZ             = 0x01
MAX30100_SAMPRATE_167HZ             = 0x02
MAX30100_SAMPRATE_200HZ             = 0x03
MAX30100_SAMPRATE_400HZ             = 0x04
MAX30100_SAMPRATE_600HZ             = 0x05
MAX30100_SAMPRATE_800HZ             = 0x06
MAX30100_SAMPRATE_1000HZ            = 0x07

MAX30100_REG_LED_CONFIGURATION      = 0x09

# LED PWM
MAX30100_PWM_200US_13BITS           = 0x00
MAX30100_PWM_400US_14BITS           = 0x01
MAX30100_PWM_800US_15BITS           = 0x02
MAX30100_PWM_1600US_16BITS          = 0x03

MAX30100_LED_CURR_0MA               = 0x00
MAX30100_LED_CURR_4_4MA             = 0x01
MAX30100_LED_CURR_7_6MA             = 0x02
MAX30100_LED_CURR_11MA              = 0x03
MAX30100_LED_CURR_14_2MA            = 0x04
MAX30100_LED_CURR_17_4MA            = 0x05
MAX30100_LED_CURR_20_8MA            = 0x06
MAX30100_LED_CURR_24MA              = 0x07
MAX30100_LED_CURR_27_1MA            = 0x08
MAX30100_LED_CURR_30_6MA            = 0x09
MAX30100_LED_CURR_33_8MA            = 0x0a
MAX30100_LED_CURR_37MA              = 0x0b
MAX30100_LED_CURR_40_2MA            = 0x0c
MAX30100_LED_CURR_43_6MA            = 0x0d
MAX30100_LED_CURR_46_8MA            = 0x0e
MAX30100_LED_CURR_50MA              = 0x0f

# Temperature

MAX30100_REG_TEMPERATURE_DATA_INT   = 0x16
MAX30100_REG_TEMPERATURE_DATA_FRAC  = 0x17

# Revision ID register (RO)
MAX30100_REG_REVISION_ID            = 0xfe

# Part ID register
MAX30100_REG_PART_ID                = 0xff

MAX30100_PART_ID                    = 0x11

MAX30100_FIFO_DEPTH                 = 0x10