package com.ahuguet.castellsenvena.core.common

object UrlEncoding {
    private const val HEX = "0123456789ABCDEF"

    /**
     * Percent-encodes [value] as a URL component (RFC 3986): only unreserved
     * characters stay as they are, spaces become `%20` and line breaks `%0A`.
     */
    fun encodeComponent(value: String): String {
        val encoded = StringBuilder()
        for (byte in value.toByteArray(Charsets.UTF_8)) {
            val code = byte.toInt() and 0xFF
            if (isUnreserved(code)) {
                encoded.append(code.toChar())
            } else {
                encoded.append('%').append(HEX[code shr 4]).append(HEX[code and 0xF])
            }
        }
        return encoded.toString()
    }

    private fun isUnreserved(code: Int): Boolean =
        code in 'A'.code..'Z'.code ||
            code in 'a'.code..'z'.code ||
            code in '0'.code..'9'.code ||
            code == '-'.code || code == '.'.code || code == '_'.code || code == '~'.code
}
