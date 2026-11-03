package io.github.ashitakalax.bridgenotifier

import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import kotlin.math.roundToInt

/**
 * The few building blocks the screens are drawn from: a scrolling page, cards,
 * text in the type scale, rows, pills. Plain framework views, no support
 * library: the app has no dependency but its own core.
 */
class Ui(val context: Context) {
    fun dp(value: Int): Int = (value * context.resources.displayMetrics.density).roundToInt()

    fun color(id: Int): Int = context.getColor(id)

    fun string(id: Int, vararg args: Any): String = context.getString(id, *args)

    /** A vertical page that scrolls, its content padded like every screen. */
    fun page(): Pair<ScrollView, LinearLayout> {
        val column = column(gap = 12)
        column.setPadding(dp(16), dp(20), dp(16), dp(20))
        val scroll = ScrollView(context)
        scroll.isFillViewport = true
        scroll.addView(column, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        return scroll to column
    }

    /** A vertical stack whose children are [gap] dp apart. */
    fun column(gap: Int = 0): LinearLayout = Stack(context, LinearLayout.VERTICAL, dp(gap))

    /** A horizontal stack, children centred vertically, [gap] dp apart. */
    fun row(gap: Int = 0): LinearLayout = Stack(context, LinearLayout.HORIZONTAL, dp(gap)).apply {
        gravity = Gravity.CENTER_VERTICAL
    }

    /** White, a hairline border, rounded corners. */
    fun card(padding: Int = 16, gap: Int = 8): LinearLayout = column(gap).apply {
        background = rounded(R.color.card, radius = 14, stroke = R.color.line)
        setPadding(dp(padding), dp(padding), dp(padding), dp(padding))
    }

    fun rounded(fill: Int, radius: Int, stroke: Int? = null): GradientDrawable = GradientDrawable().apply {
        setColor(color(fill))
        cornerRadius = dp(radius).toFloat()
        if (stroke != null) setStroke(dp(1), color(stroke))
    }

    fun text(
        value: CharSequence = "",
        size: Float = 14f,
        color: Int = R.color.ink,
        bold: Boolean = false,
        mono: Boolean = false,
    ): TextView = TextView(context).apply {
        text = value
        setTextSize(TypedValue.COMPLEX_UNIT_SP, size)
        setTextColor(this@Ui.color(color))
        typeface = Typeface.create(if (mono) Typeface.MONOSPACE else Typeface.SANS_SERIF, if (bold) Typeface.BOLD else Typeface.NORMAL)
        setLineSpacing(0f, 1.15f)
    }

    /** The small uppercase line over a screen's title. */
    fun eyebrow(value: CharSequence): TextView = text(value, size = 12f, color = R.color.muted, bold = true).apply {
        isAllCaps = true
        letterSpacing = 0.06f
    }

    fun title(value: CharSequence): TextView = text(value, size = 24f, bold = true)

    /** A section's label inside a card. */
    fun label(value: CharSequence): TextView = text(value, size = 13f, color = R.color.ink_soft, bold = true)

    /** A round status mark: ✓, !, ✗ or ? on its colour. */
    fun mark(symbol: String, fill: Int): TextView = text(symbol, size = 13f, color = R.color.card, bold = true).apply {
        gravity = Gravity.CENTER
        background = GradientDrawable().apply {
            shape = GradientDrawable.OVAL
            setColor(color(fill))
        }
        layoutParams = LinearLayout.LayoutParams(dp(24), dp(24))
    }

    /** A filled or outlined button, at least 48 dp tall. */
    fun button(value: CharSequence, filled: Boolean, onClick: () -> Unit): Button = Button(context).apply {
        text = value
        isAllCaps = false
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
        typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
        minHeight = dp(48)
        stateListAnimator = null
        setTextColor(color(if (filled) R.color.card else R.color.accent))
        background = rounded(if (filled) R.color.accent else R.color.card, radius = 12, stroke = R.color.accent)
        setOnClickListener { onClick() }
    }

    /** A toggle chip: selected is filled with the accent. */
    fun chip(value: CharSequence, selected: Boolean, onClick: () -> Unit): TextView =
        text(value, size = 13f, color = if (selected) R.color.card else R.color.ink_soft, bold = selected).apply {
            gravity = Gravity.CENTER
            minHeight = dp(40)
            setPadding(dp(14), 0, dp(14), 0)
            background = rounded(if (selected) R.color.accent else R.color.card, radius = 20, stroke = if (selected) R.color.accent else R.color.line_strong)
            isClickable = true
            isFocusable = true
            contentDescription = value
            isSelected = selected
            setOnClickListener { onClick() }
        }

    /** A view that takes the rest of a row. */
    fun grow(view: View): View = view.apply {
        layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
    }

    /** Spaces its children [gap] apart, the way a CSS flex gap does. */
    private class Stack(context: Context, orientation: Int, private val gap: Int) : LinearLayout(context) {
        init {
            this.orientation = orientation
        }

        override fun addView(child: View, index: Int, params: ViewGroup.LayoutParams) {
            val lp = params as? LayoutParams ?: generateLayoutParams(params)
            if (childCount > 0 && gap > 0) {
                if (orientation == VERTICAL) lp.topMargin = gap else lp.marginStart = gap
            }
            if (orientation == VERTICAL && lp.width == ViewGroup.LayoutParams.WRAP_CONTENT && params !is LayoutParams) {
                lp.width = ViewGroup.LayoutParams.MATCH_PARENT
            }
            super.addView(child, index, lp)
        }
    }
}
