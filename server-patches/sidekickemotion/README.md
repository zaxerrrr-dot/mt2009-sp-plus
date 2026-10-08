# Emocje z Towarzyszem (MT2009_PLUS_SIDEKICK_EMOTIONS_V1)

Prośba właściciela (8 października 2026): „Dodaj możliwość emocji z towarzyszem, domyślnie włączone”.

## Co robi

| Część | Jak |
|---|---|
| Zgoda na emocje we dwoje | pocałunek, francuski pocałunek i klepnięcie wymagają zgody drugiej strony (przycisk „Zezwól na emocje” w oknie celu, `/emotion_allow <vid>`). Przy włączonych „Emocjach” Towarzysz ma tę zgodę dla swojego właściciela zawsze, gdy są na jednej mapie – bez zmiany silnika (para w `s_emotion_set`, `playerbot_sidekick.h`). Zasady silnika zostają: pocałunki tylko z drugą płcią, 10–500 jednostek odstępu, nikt na koniu, maska emocji albo premium |
| Odpowiedź Towarzysza | po emocji właściciela na nim (pocałunek → zawstydzenie / radość, klepnięcie → złość / smutek) albo obok niego (taniec → ten sam taniec, oklaski / wiwat → oklaski albo wiwat, smutek → otucha…) Towarzysz czasem odpowiada emocją po 1–4 s (nie częściej niż co 20 s; na emocje solo w 60% przypadków) i czasem krótkim szeptem (nie częściej niż co 90 s) |
| Ustawienie | `player.playerbot_sidekick.emotions` (1 = włączone, domyślnie); szept „emocje on” / „emocje off” (też „włącz/wyłącz emocje”, „bez emocji”), komenda `/towarzysz emocje 1|0`, w oknie Towarzysza przycisk na pasku „Walka” (klient 2.0.30) |

## Zmiana silnika (`edits.json`)

Jedno wywołanie w `do_emotion` (`cmd_emotion.cpp`) po wysłaniu emocji:
`PlayerBotSidekickOnEmotion(ch, victim, emotion_types[i].command_to_client)` – tylko po to, żeby Towarzysz mógł
odpowiedzieć. Bez tej zmiany zgoda na emocje we dwoje działa, odpowiedzi nie ma.

Nakładanie: `tools/port/Apply-MT2009PlusEngine.ps1` (po digirasta-qol) albo bliźniaki
`Apply-SidekickEmotionPatch.ps1 -SourceDir <game/src>` / `python3 apply_sidekick_emotion.py <game/src>`.
Plik ma końce linii CRLF – edycja wchodzi z takimi, z jakimi została znaleziona.
