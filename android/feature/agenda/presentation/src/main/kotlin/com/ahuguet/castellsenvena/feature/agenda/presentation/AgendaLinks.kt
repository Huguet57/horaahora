package com.ahuguet.castellsenvena.feature.agenda.presentation

import com.ahuguet.castellsenvena.core.common.UrlEncoding

/** A Google Maps search for the venue of an event. */
fun googleMapsSearchUrl(venue: String, municipality: String): String =
    "https://www.google.com/maps/search/?api=1&query=" + UrlEncoding.encodeComponent("$venue, $municipality")
