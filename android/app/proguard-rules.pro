# kotlinx.serialization: keep the generated serializers of the API models.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keepclassmembers class com.ahuguet.castellsenvena.** {
    *** Companion;
}
-keepclasseswithmembers class com.ahuguet.castellsenvena.** {
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.ahuguet.castellsenvena.**$$serializer { *; }
