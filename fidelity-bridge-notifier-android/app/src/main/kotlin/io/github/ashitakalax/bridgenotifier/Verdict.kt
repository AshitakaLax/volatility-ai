package io.github.ashitakalax.bridgenotifier

import io.github.ashitakalax.bridgenotifier.core.Account
import io.github.ashitakalax.bridgenotifier.core.BridgeClient
import io.github.ashitakalax.bridgenotifier.core.Broker
import io.github.ashitakalax.bridgenotifier.core.TraderStatus

/**
 * An account's state in a few words, on its colour: Home's banner, and each
 * card on the All accounts page. For Fidelity, ready to trade or the one
 * thing to fix; for Alpaca, what its trader says it is doing; for either,
 * the connection first when there is none.
 */
data class Verdict(val fill: Int, val tag: String, val title: String, val detail: String) {
    companion object {
        fun of(ui: Ui, account: Account?, state: MonitorState.AccountState): Verdict {
            val host = state.status.bridge
            val link = state.link
            val where = account?.name ?: ""
            return when {
                link is BridgeClient.Link.Refused -> Verdict(R.color.status_bad, ui.string(R.string.hero_offline_tag), ui.string(R.string.hero_refused_title), link.reason)
                link is BridgeClient.Link.Waiting && link.deliberate -> Verdict(R.color.status_offline, ui.string(R.string.hero_offline_tag), ui.string(R.string.hero_restarting_title, where), link.reason)
                link is BridgeClient.Link.Waiting -> Verdict(R.color.status_offline, ui.string(R.string.hero_offline_tag), ui.string(R.string.hero_offline_title, where), link.reason)
                link == BridgeClient.Link.Connecting -> Verdict(R.color.status_offline, ui.string(R.string.hero_connecting_tag), ui.string(R.string.hero_connecting_title, MonitorService.hostOf(account?.url ?: "")), "")
                link !is BridgeClient.Link.Connected -> Verdict(R.color.status_offline, ui.string(R.string.hero_idle_tag), ui.string(R.string.hero_idle_title), ui.string(R.string.hero_idle_detail))
                // An Alpaca deployment has no bridge to be ready: its trader says how it is.
                host == null && (account?.broker == Broker.ALPACA || state.status.trader != null) -> trader(ui, state.status.trader)
                host == null -> Verdict(R.color.status_offline, ui.string(R.string.hero_unknown_tag), ui.string(R.string.hero_unknown_title), ui.string(R.string.hero_unknown_detail))
                host.ready -> Verdict(R.color.status_ok, ui.string(R.string.hero_ready_tag), ui.string(R.string.hero_ready_title), ui.string(R.string.hero_ready_detail))
                else -> Verdict(R.color.status_bad, ui.string(R.string.hero_blocked_tag), host.summary, host.fix?.let { ui.string(R.string.hero_fix, it) }.orEmpty())
            }
        }

        /** What the trader of an Alpaca deployment says it is doing. */
        private fun trader(ui: Ui, trader: TraderStatus?): Verdict {
            if (trader == null) {
                return Verdict(R.color.status_offline, ui.string(R.string.hero_unknown_tag), ui.string(R.string.hero_unreported_title), ui.string(R.string.hero_unreported_detail))
            }
            val words = trader.state.replace('_', ' ')
            val said = listOfNotNull(words, trader.detail).joinToString(": ")
            val ago = { iso: String? -> Format.ago(iso) ?: ui.string(R.string.unknown) }
            if (trader.stale) {
                val quietly = trader.state in setOf("stopped", "disabled")
                return Verdict(
                    if (quietly) R.color.status_offline else R.color.status_bad,
                    ui.string(R.string.hero_quiet_tag),
                    ui.string(R.string.hero_quiet_title),
                    ui.string(R.string.hero_quiet_detail, ago(trader.updatedAt), said),
                )
            }
            val detail = trader.detail.orEmpty()
            return when (trader.state) {
                "trading" -> Verdict(R.color.status_ok, ui.string(R.string.hero_trading_tag), ui.string(R.string.hero_trading_title), detail.takeIf { it != "trading" }.orEmpty())
                "starting" -> Verdict(R.color.status_ok, ui.string(R.string.hero_starting_tag), ui.string(R.string.hero_starting_title), detail)
                "winding_down" -> Verdict(R.color.status_warn, ui.string(R.string.hero_winding_tag), ui.string(R.string.hero_winding_title), detail)
                "buys_paused" -> Verdict(R.color.status_warn, ui.string(R.string.hero_paused_tag), detail.ifEmpty { ui.string(R.string.hero_paused_title) }, "")
                "waiting_for_broker", "restarting" -> Verdict(R.color.status_warn, ui.string(R.string.hero_trader_tag), words.replaceFirstChar(Char::uppercase), detail)
                "recovery_required" -> Verdict(R.color.status_bad, ui.string(R.string.hero_recovery_tag), ui.string(R.string.hero_recovery_title), detail)
                "stopping", "stopped" -> Verdict(R.color.status_offline, ui.string(R.string.hero_stopped_tag), ui.string(R.string.hero_stopped_title), detail)
                "waiting_for_open" -> Verdict(
                    R.color.status_offline,
                    ui.string(R.string.hero_waiting_tag),
                    ui.string(R.string.hero_waiting_title),
                    trader.nextOpen?.let { ui.string(R.string.hero_waiting_detail, ago(it)) } ?: detail,
                )
                else -> Verdict(R.color.status_offline, ui.string(R.string.hero_trader_tag), words.replaceFirstChar(Char::uppercase), detail)
            }
        }

        /**
         * How fresh what the app shows for an account is: live while
         * connected, else when its listener was last heard -- in this run,
         * or as kept from the last one ([kept]).
         */
        fun freshness(ui: Ui, state: MonitorState.AccountState, kept: Long?): Pair<String, Int> = when {
            state.link is BridgeClient.Link.Connected -> ui.string(R.string.fresh_live) to R.color.status_ok
            else -> (state.heardAt ?: kept)?.let { ui.string(R.string.fresh_heard, Format.relative(it)) to R.color.status_warn }
                ?: (ui.string(R.string.fresh_never) to R.color.muted)
        }
    }
}
