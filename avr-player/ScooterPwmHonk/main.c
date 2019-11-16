/*
 * ScooterPwmHonk.c
 *
 * Created: 09/11/2019 17:03:23
 * Author : Marcos
 */ 

#include <avr/io.h>
#include <avr/cpufunc.h> 
#include <stdbool.h>
#include <stdint.h>
#include "samples.h"

const int8_t PROGMEM INDEX_TABLE[] = {
	-1, -1, -1, -1, 2, 4, 6, 8
};

const uint8_t PROGMEM STEP_TABLE[] = {
	7, 8, 8, 9, 10, 11, 12, 14, 15, 17, 18, 20, 22, 24, 27, 29, 32, 35, 39, 43, 47, 52, 57, 63, 69, 76, 83, 92, 101, 111, 122
};

const uint8_t * adpcmOffset;
uint16_t adpcmLen = 0;
bool adpcmIsOdd = false;
uint8_t adpcmPredicted;
int8_t adpcmIndex;

void adpcm_step() {
	if (adpcmLen == 0) {
		adpcmOffset = goose_01;
		adpcmPredicted = pgm_read_byte(adpcmOffset);
		adpcmOffset++;
		adpcmIndex = pgm_read_byte(adpcmOffset);
		adpcmOffset++;
		adpcmLen = goose_01_size - 2;
		adpcmIsOdd = false;
	} else {
		uint8_t sample = pgm_read_byte(adpcmOffset);
		if (adpcmIsOdd) {
			sample = sample >> 4;
			adpcmOffset++;
			adpcmLen--;
		}
		adpcmIsOdd = !adpcmIsOdd;

		uint8_t step = pgm_read_byte(&STEP_TABLE[adpcmIndex]);

		uint8_t predictedDelta = 0;
		if (sample & 4) {
			predictedDelta = step;
		}

		step >>= 1;
		if (sample & 2) {
			predictedDelta += step;
		}

		step >>= 1;
		if (sample & 1) {
			predictedDelta += step;
		}

		step >>= 1;
		predictedDelta += step;

		if (sample & 8) {
			if (predictedDelta >= adpcmPredicted) {
				adpcmPredicted = 0;
			} else {
				adpcmPredicted -= predictedDelta;
			}
		} else {
			adpcmPredicted += predictedDelta;
			if (adpcmPredicted < predictedDelta) {
				adpcmPredicted = 255;
			}
		}

		adpcmIndex += pgm_read_byte(&INDEX_TABLE[sample & 7]);
		if (adpcmIndex < 0) {
			adpcmIndex = 0;
		} else if (adpcmIndex >= sizeof(STEP_TABLE)) {
			adpcmIndex = sizeof(STEP_TABLE) - 1;
		}
	}

	OCR0A = adpcmPredicted;
}

int main(void) {
	// Mark output on OC0A
	DDRB = 0b000000001;

	// Init
	adpcm_step();

	// Enable PWM with non-inverting output on COM0A
	TCCR0A = 1 << COM0A1 | 1 << WGM01 | 1 << WGM00;

	// Enable clock with no prescaler
	TCCR0B = 1 << CS00;

	// Wait for a bit before loading next sample, which will be buffered so it'll get updated on counter overflow
	_NOP();
	_NOP();
	adpcm_step();

	while (1) {
		if (TIFR & (1 << OCF0A)) {
			TIFR |= (1 << OCF0A);
			adpcm_step();
		}
	}
}
