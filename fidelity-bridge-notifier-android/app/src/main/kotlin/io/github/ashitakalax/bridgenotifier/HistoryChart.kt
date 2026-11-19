package io.github.ashitakalax.bridgenotifier

import android.annotation.SuppressLint
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import android.view.MotionEvent
import android.view.View
import io.github.ashitakalax.bridgenotifier.core.DayFigures
import java.time.format.DateTimeFormatter
import java.util.Locale
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * Each trading day's realised profit as a bar, up green and down red about
 * a zero line, oldest on the left. Touching it picks the day under the
 * finger ([onPick]); the latest is picked to start with.
 */
@SuppressLint("ViewConstructor")
class HistoryChart(private val ui: Ui) : View(ui.context) {
    var days: List<DayFigures> = emptyList()
        set(value) {
            val keep = picked?.let { field.getOrNull(it)?.date }
            field = value
            picked = value.indexOfFirst { it.date == keep }.takeIf { it >= 0 } ?: value.lastIndex.takeIf { it >= 0 }
            contentDescription = describe(value)
            invalidate()
        }

    /** The day picked, or null with none to pick. */
    var onPick: ((DayFigures?) -> Unit)? = null

    private var picked: Int? = null

    val pickedDay: DayFigures? get() = picked?.let(days::getOrNull)

    private val up = paint(R.color.status_ok)
    private val down = paint(R.color.status_bad)
    private val zero = paint(R.color.line_strong)
    private val cursor = paint(R.color.ink_soft)
    private val label = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ui.color(R.color.muted)
        textSize = ui.dp(11).toFloat()
        typeface = Typeface.MONOSPACE
    }
    private val dateFormat = DateTimeFormatter.ofPattern("MMM d", Locale.US)

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        setMeasuredDimension(MeasureSpec.getSize(widthMeasureSpec), resolveSize(ui.dp(150), heightMeasureSpec))
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val labels = label.textSize + ui.dp(4)
        val top = labels
        val bottom = height - labels
        val values = days.map { it.realized }
        val high = max(0.0, values.maxOrNull() ?: 0.0)
        val low = min(0.0, values.minOrNull() ?: 0.0)
        val span = (high - low).takeIf { it > 0 } ?: 1.0
        val zeroY = (top + (bottom - top) * (high / span)).toFloat()
        canvas.drawRect(0f, zeroY - ui.dp(1) / 2f, w, zeroY + ui.dp(1) / 2f, zero)
        if (days.isEmpty()) return

        val slot = w / days.size
        val gap = min(slot * 0.25f, ui.dp(3).toFloat())
        days.forEachIndexed { index, day ->
            val x0 = index * slot + gap / 2
            val x1 = x0 + slot - gap
            val y = (zeroY - (day.realized / span) * (bottom - top)).toFloat()
            // A day that made nothing still shows it traded: a sliver on the line.
            val (y0, y1) = if (abs(y - zeroY) < ui.dp(2)) zeroY - ui.dp(1) to zeroY + ui.dp(1) else min(y, zeroY) to max(y, zeroY)
            val paint = if (day.realized < 0) down else up
            paint.alpha = if (index == picked) 255 else 170
            canvas.drawRect(x0, y0, max(x1, x0 + 1f), y1, paint)
        }
        picked?.let { index ->
            val x = index * slot + slot / 2
            canvas.drawRect(x - ui.dp(1) / 2f, top, x + ui.dp(1) / 2f, bottom, cursor.apply { alpha = 90 })
        }

        // The scale, top and bottom, and the first and last days.
        canvas.drawText(Format.signedMoney(high), 0f, label.textSize, label)
        if (low < 0) canvas.drawText(Format.signedMoney(low), 0f, bottom + label.textSize + ui.dp(2), label)
        val last = dateFormat.format(days.last().date)
        canvas.drawText(last, w - label.measureText(last), bottom + label.textSize + ui.dp(2), label)
        if (days.size > 1 && low >= 0) canvas.drawText(dateFormat.format(days.first().date), 0f, bottom + label.textSize + ui.dp(2), label)
    }

    @SuppressLint("ClickableViewAccessibility") // the days are read out from contentDescription
    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (days.isEmpty()) return false
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                // Sliding along the bars picks each in turn, rather than scrolling the page.
                parent?.requestDisallowInterceptTouchEvent(true)
                val index = (event.x / (width.toFloat() / days.size)).toInt().coerceIn(0, days.lastIndex)
                if (index != picked) {
                    picked = index
                    invalidate()
                    onPick?.invoke(days[index])
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> parent?.requestDisallowInterceptTouchEvent(false)
        }
        return true
    }

    private fun describe(days: List<DayFigures>): String {
        if (days.isEmpty()) return ui.string(R.string.history_empty)
        val total = days.sumOf { it.realized }
        return ui.string(R.string.history_description, days.size, Format.signedMoney(total))
    }

    private fun paint(color: Int) = Paint(Paint.ANTI_ALIAS_FLAG).apply { this.color = ui.color(color) }
}
