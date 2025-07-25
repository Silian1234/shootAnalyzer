[app]
title             = ShootAnalyzer
package.name       = shootanalyzer
package.domain     = org.example
version            = 0.1

source.dir         = .
source.main        = gui.py
icon.filename = icon.png
requirements       = kivy,kivymd,opencv,plyer,requests,numpy,cython,https://github.com/kivy/pyjnius/archive/master.zip,tflite-runtime

android.archs      = arm64-v8a
android.api        = 31
android.minapi     = 21
orientation        = portrait

android.enable_androidx = 1
android.gradle_dependencies = androidx.core:core:1.8.0,androidx.annotation:annotation-experimental:1.2.0
android.add_resource = res/xml/fileprovider_paths.xml

android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

source.include_exts = py,png,jpg,tflite,json,yaml,npy,pdf