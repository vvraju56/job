# Add project specific ProGuard rules here.
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# Keep Firebase/Messaging service names
-keep class com.google.firebase.** { *; }
-keep class com.makeable.jobs.** { *; }