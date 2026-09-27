package com.ahuguet.castellsenvena.feature.scoretable.presentation

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ScoreBarAxisTest {
    private val top = castell("3de10sm", loaded = 6_205, unloaded = 7_475)
    private val middle = castell("9de9f", loaded = 4_295, unloaded = 5_180)
    private val bottom = castell("5de9f", loaded = 2_595, unloaded = 3_125)
    private val below = castell("7de9f", loaded = 2_500, unloaded = 3_010)

    @Test
    fun theWindowFillsTheBarFromNearTheLeftToTheRight() {
        val axis = axis(top to 1.0, middle to 1.0, bottom to 1.0)

        assertEquals(1.0, axis.fraction(7_475))
        assertEquals(ScoreBarAxis.LEADING_FRACTION, axis.fraction(2_595), 0.000_1)
        assertTrue(axis.fraction(2_595) < axis.fraction(3_125))
    }

    @Test
    fun aPartlyVisibleCastellWeighsInProportion() {
        val whole = axis(top to 1.0, middle to 1.0, bottom to 1.0)
        val entering = axis(top to 1.0, middle to 1.0, bottom to 1.0, below to 0.5)
        val inside = axis(top to 1.0, middle to 1.0, bottom to 1.0, below to 1.0)

        assertTrue(inside.lowerBound < entering.lowerBound)
        assertTrue(entering.lowerBound < whole.lowerBound)
        assertEquals((whole.lowerBound + inside.lowerBound) / 2, entering.lowerBound, 0.001)
    }

    @Test
    fun theScaleDoesNotJumpWhenACastellEntersOrLeaves() {
        val without = axis(middle to 1.0, bottom to 1.0)
        val barelyIn = axis(top to 0.001, middle to 1.0, bottom to 1.0)
        val almostIn = axis(top to 0.999, middle to 1.0, bottom to 1.0)
        val with = axis(top to 1.0, middle to 1.0, bottom to 1.0)

        assertEquals(without.upperBound, barelyIn.upperBound, 3.0)
        assertEquals(with.upperBound, almostIn.upperBound, 3.0)
    }

    @Test
    fun castellsOffScreenDoNotCount() {
        assertEquals(5_180.0, axis(top to 0.0, middle to 1.0, bottom to 1.0).upperBound)
        assertNull(ScoreBarAxis.forVisible(listOf(top to 0.0)))
    }

    @Test
    fun valuesOutsideTheWindowStayWithinTheBar() {
        val axis = axis(middle to 1.0, bottom to 1.0)

        assertEquals(1.0, axis.fraction(7_475))
        assertEquals(0.0, axis.fraction(250))
    }

    @Test
    fun theWholeTableIsTheStartingScale() {
        val axis = ScoreBarAxis.forCastells(ScoreTable.bundled().castells)

        assertEquals(7_475.0, axis.upperBound)
        assertEquals(ScoreBarAxis.LEADING_FRACTION, axis.fraction(250), 0.000_1)
    }

    @Test
    fun aRowCountsWholeInsideTheWindowAndFadesOutsideIt() {
        fun weight(y: Float) = ScoreBarAxis.weight(rowTop = y, windowTop = 200f, windowBottom = 700f, fadeAbove = 40f, fadeBelow = 40f)

        assertEquals(1.0, weight(450f))
        assertEquals(1.0, weight(200f))
        assertEquals(1.0, weight(199.5f), "Rounding does not hide a row at rest")
        assertEquals(0.5, weight(179f), 0.001)
        assertEquals(0.0, weight(150f))
        assertEquals(0.5, weight(720f), 0.001)
        assertEquals(0.0, weight(800f))
    }

    private fun axis(vararg visible: Pair<ScoreTableCastell, Double>): ScoreBarAxis =
        assertNotNull(ScoreBarAxis.forVisible(visible.toList()))

    private fun castell(notation: String, loaded: Int, unloaded: Int) =
        ScoreTableCastell(notation, notation, group = 7, loaded = loaded, unloaded = unloaded)
}
