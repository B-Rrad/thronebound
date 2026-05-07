import pygame


class AudioMixin:
    def _start_music(self):
        if not self.music_tracks:
            return

        try:
            pygame.mixer.init()
            pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)
        except pygame.error:
            self.music_enabled = False
            return

        self.music_enabled = True
        self.music_index = 0
        self._play_music_track(self.music_index)

    def _play_music_track(self, track_index):
        if not self.music_enabled or not self.music_tracks:
            return

        track_count = len(self.music_tracks)
        for offset in range(track_count):
            candidate_index = (track_index + offset) % track_count
            track_path = self.music_tracks[candidate_index]
            try:
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()
                self.music_index = candidate_index
                return
            except pygame.error:
                continue

        self.music_enabled = False

    def _advance_music(self):
        if not self.music_enabled or not self.music_tracks:
            return

        self._play_music_track(self.music_index + 1)

