ESP-Docs Simple Example
=========================
:link_to_translation:`zh_CN:[中文]`

This is a simple example for the esp-docs building system.

Wavedrom Example
----------------

.. wavedrom::

        { "signal": [
                { "name": "clk",  "wave": "P......" },
                { "name": "bus",  "wave": "x.==.=x", "data": ["head", "body", "tail", "data"] },
                { "name": "wire", "wave": "0.1..0." }
        ]}


.. wavedrom:: /../_static/periph_timing.json

Blockdiag Example
-----------------

.. blockdiag::
    :scale: 100%
    :caption: Blockdiagram
    :align: center

    blockdiag esp-docs-block-diag {
        Start -> Middle
        Middle -> End
    }

For documentation about esp-docs please see https://github.com/espressif/esp-docs/tree/master/docs

.. toctree::
    :maxdepth: 1

    Subpage <subpage>

Wokwi embed example
===================

.. wokwi-tabs::

  .. code-block:: arduino
    :name: Code2

    #define LED    12
    #define BUTTON 2

    uint8_t stateLED = 0;

      void setup() {
          pinMode(LED, OUTPUT);
          pinMode(BUTTON,INPUT_PULLUP);
      }

      void loop() {

        if(!digitalRead(BUTTON)){
          stateLED = stateLED^1;
          digitalWrite(LED,stateLED);
        }
      }

  .. wokwi::
    :name: ESP32
    :diagram: https://it.kubaandrysek.cz/wokwi/gpio-basic-s3.json
    :firmware: https://it.kubaandrysek.cz/wokwi/gpio-basic-s3.bin

  .. wokwi::
    :name: ESP32-C3
    :diagram: https://it.kubaandrysek.cz/wokwi/gpio-basic-s3.json
    :firmware: https://it.kubaandrysek.cz/wokwi/gpio-basic-s3.bin
