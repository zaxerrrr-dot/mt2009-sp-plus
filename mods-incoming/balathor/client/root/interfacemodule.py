# Add

if app.__BALATHOR__:
	import uiGuildWhiteDragon

# Search

		systemSetting.SetInterfaceHandler(self)

# Add after

		if app.__BALATHOR__:
			self.wndBalathorInfo = None
			self.wndBalathorScreenEffect = None

# Search

	def Close(self):

# Add after

		if app.__BALATHOR__:
			if self.wndBalathorInfo:
				self.wndBalathorInfo.Destroy()
				self.wndBalathorInfo = None
			if self.wndBalathorScreenEffect:
				self.wndBalathorScreenEffect.Destroy()
				self.wndBalathorScreenEffect = None

# Add

	if app.__BALATHOR__:
		def SetBalathorEffect(self, wave_count):
			if not self.wndBalathorScreenEffect:
				self.wndBalathorScreenEffect = uiGuildWhiteDragon.ScreenEffect()
			self.wndBalathorScreenEffect.AddWave(int(wave_count))

		def SetBalathor(self, balathor_hp, balathor_maxhp, balathor_rage, balathor_rage_max, egg_fail_count, hwatcha_count, hwatcha_hp, hwatcha_maxhp):
			if not self.wndBalathorInfo:
				self.wndBalathorInfo = uiGuildWhiteDragon.Window()
			self.wndBalathorInfo.Set(int(balathor_hp), int(balathor_maxhp), int(balathor_rage), int(balathor_rage_max), int(egg_fail_count), int(hwatcha_count), int(hwatcha_hp), int(hwatcha_maxhp))
