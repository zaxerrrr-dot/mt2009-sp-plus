quest __balathor__ begin
	state start begin

		function check_config()
			local balathor_config = {balathor.get_register_config()}
			local min_level = balathor_config[1]
			local min_guild_level = balathor_config[2]
			local min_member_count = balathor_config[3]
			local max_member_count = balathor_config[4]
			local ladder_point = balathor_config[5]
			local ticket_vnum = balathor_config[6]
			local wait_time = balathor_config[7]

			--say("Min Level: "..min_level)
			--say("Min Guild Level: "..min_guild_level)
			--say("Min Member Count: "..min_member_count)
			--say("Max Member Count: "..max_member_count)
			--say("Ladder Point: "..ladder_point)
			--say("Ticket Vnum: "..ticket_vnum)
			--say("Wait Time: "..wait_time)

			if pc.is_guild_master() == false then
				say("Only guild leader can register!")
				return false
			end

			local guild_id = pc.get_guild()

			local leftTime = guild.get_flag("balathor_cooldown") - get_global_time()
			if leftTime > 0 then
				say(string.format("You can join after %d sec", leftTime))
				return false
			end

			if guild.get_flag("balathor_channel") != 0 then
				say("You already has a active dungeon")
				return false
			end

			if guild.get_near_count() < min_member_count then
				say(string.format("You need near %d guild member", min_member_count))
				return false
			end

			if guild.get_level() < min_guild_level then
				say(string.format("Guild level should minimum %d", min_guild_level))
				return false
			end

			if guild.get_ladder_point() < ladder_point then
				say(string.format("Guild not has enough ladder point, min: %d", ladder_point))
				return false
			end

			local pids = { guild.get_near_pids() }
			local notEnoughLevelMembers = {}
			local noTicketMembers = {}
			local levelCheck = true
			local ticketCheck = true
			
			for i, pid in next, pids, nil do
				q.begin_other_pc_block(pid)

				-- Level check
				if pc.get_level() < min_level then
					table.insert(notEnoughLevelMembers, pc.get_name())
					levelCheck = false
				end

				-- Ticket check
				if ticket_vnum != 0 then
					if pc.count_item(ticket_vnum) == 0 then
						table.insert(noTicketMembers, pc.get_name())
						ticketCheck = false
					end
				end

				q.end_other_pc_block()
			end

			if not levelCheck then
				say(string.format("One of your near guild member not match min level %d", min_level))
				return false
			end

			if ticket_vnum != 0 and not ticketCheck then
				say("At least one player does not have a passage ticket.")
				for i, name in next, noTicketMembers, nil do
					say(" " .. name)
				end
				return false
			end

			local result = balathor.can_create()
			if result == 0 then
				say("You don't have guild.")
				return false
			elseif result == 1 then
				say("You already has a balathor dungeon")
				return false
			elseif result == 2 then
				say("Balathor main map not exist, please contact game master!")
				return false
			end

			if ticket_vnum != 0 then
				for i, pid in next, pids, nil do
					q.begin_other_pc_block(pid)

					if pc.count_item(ticket_vnum) >= 1 then
						pc.remove_item(ticket_vnum, 1)
						q.end_other_pc_block()
						break
					end

					q.end_other_pc_block()
				end
			end

			guild.set_flag("balathor_channel", pc.get_channel_id())
			guild.set_flag("balathor_cooldown", get_global_time() + wait_time)
			balathor.create()

			return true
		end

		when 20395.chat."Register Balathor" with pc.get_map_index() == 61 begin
			say_title(mob_name(20395))
			say("")
			say("Do you wanna register?")
			local x = select("Yes", "No")
			if x == 1 then
				if __balathor__.check_config() == true then
					say("Created successfully")
				end
			end
		end

		when 20395.chat."GM: Reset Cooldown" with pc.get_map_index() == 61 and pc.is_gm() == true and guild.get_flag("balathor_cooldown") != 0 begin
			if guild.get_flag("balathor_channel") != 0 then
				say("You can't reset cooldown while has dungeon")
				return
			end
			guild.set_flag("balathor_cooldown", 0)
			say("Reset success")
		end

		when 20395.chat."Join Balathor" with pc.get_map_index() == 61 and guild.get_flag("balathor_channel") != 0 begin
			say_title(mob_name(20395))
			say("")
		
			if pc.has_guild() == false then
				say("You don't have guild")
				return
			end
		
			if guild.get_flag("balathor_channel") != pc.get_channel_id() then
				say(string.format("Your channel created in %d please try in same channel", balathor_channel))
				return
			end
		
			if balathor.is_guild_dungeon_exist(pc.get_guild()) == false then
				say("Dungeon not exist!")
				guild.set_flag("balathor_channel", 0)
				return
			end
			
			local balathor_config = {balathor.get_register_config()}
			local min_level = balathor_config[1]

			if pc.get_level() < min_level then
				say(string.format("You don't have enough level %d", min_level))
				return
			end

			say("Do you wanna join?")
			local x = select("Yes", "No")
			if x == 1 then
				balathor.teleport()
			end
		end

		when 20815.chat."To the Balathor" with balathor.is_in_map(pc.get_map_index()) == true and balathor.get_stage(pc.get_map_index()) == 1 begin
			say_title(mob_name(20815))
			say("")
			if pc.isguildmaster() == false then
				say("Only guild leader can start")
				return
			end
			say("Do you want start run?")
			local x = select("Yes", "Cancel")
			if x == 1 then
				say_title(mob_name(20815))
				say("")
				say("Good Luck!")
				balathor.set_stage(pc.get_map_index(), 2)
			end
		end

		when 20815.chat."Leave" with balathor.is_in_map(pc.get_map_index()) == true begin
			say_title(mob_name(20815))
			say("")
			say("Do you want leave?")
			local x = select("Yes", "Cancel")
			if x == 1 then
				say_title(mob_name(20815))
				say("")
				balathor.warp_enter()
			end
		end
		
		when 20815.chat."Give Up" with balathor.is_in_map(pc.get_map_index()) == true and balathor.get_stage(pc.get_map_index()) >= 2 and balathor.get_stage(pc.get_map_index()) <= 6 begin
			say_title(mob_name(20815))
			say("")
			if pc.isguildmaster() == false then
				say("Only guild leader can give up")
				return
			end
			say("Do you want give up?")
			local x = select("Yes", "Cancel")
			if x == 1 then
				say_title(mob_name(20815))
				say("")
				say("Give up success")
				balathor.give_up()
			end
		end

		when 20492.chat."Claim Reward" with balathor.is_in_map(pc.get_map_index()) == true begin
			say_title(mob_name(20815))
			say("")
			say("Do you want claim reward?")
			local x = select("Yes", "Cancel")
			if x == 1 then
				say_title(mob_name(20815))
				say("")

				local reward_result = balathor.claim_reward(pc.get_map_index())
				if reward_result == 0 then
					say("You already claim reward")
					return
				elseif reward_result == 1 then
					say("You cannot reward in this phase.")
					return
				end
				say("Reward claimed successfully.")
			end
		end

		when 20493.click with balathor.is_in_map(pc.get_map_index()) == true begin
			if balathor.is_hwatcha_dead(pc.get_map_index()) == true then
				local x = select("Revive", "Cancel")
				if x == 1 then
					balathor.revive_hwatcha(pc.get_map_index())
				end
			else
				local x = select("Fire", "Cancel")
				if x == 1 then
					if balathor.can_use_hwatcha(pc.get_map_index()) == true then
						balathor.use_hwatcha(pc.get_map_index())
					else
						say("You can't use right now.")
					end
				end
			
			end
		end
	end
end
