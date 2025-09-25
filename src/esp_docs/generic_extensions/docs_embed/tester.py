from esp_docs.generic_extensions.docs_embed.tool.wokwi_tool import DiagramSync

if __name__ == "__main__":
    sync = DiagramSync("/Users/kuba/Documents/Arduino/hardware/espressif/esp32/libraries/ESP32/examples/GPIO/BlinkRGB")
    platforms_list = ["esp32", "esp32s2", "esp32s3"]
    diagram = True
    ci = False
    override = True

    sync.init_project(platforms_list, diagram, ci, override)
