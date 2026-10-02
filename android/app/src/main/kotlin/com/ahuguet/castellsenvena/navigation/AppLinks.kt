package com.ahuguet.castellsenvena.navigation

/** What the screens ask of the platform: opening links, email and the clipboard. */
interface AppLinks {
    /** A web page shown on top of the app, like the iOS in-app browser. */
    fun openInApp(url: String)

    fun composeEmail(mailtoUrl: String)

    fun copyToClipboard(text: String)
}
