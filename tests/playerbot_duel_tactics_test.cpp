#include "../linux-port/overlays/playerbot/src/game/src/playerbot_pvp_policy.h"
#include <cassert>
#include <iostream>

int main() {
    using namespace playerbot_duel;
    // UseSkill owns self-only attacks, Charge and Summon Lightning. A manual
    // follow-up for these would duplicate the engine's real dispatch.
    assert(EngineComputesSkill(true,false,false,false,false));
    assert(EngineComputesSkill(false,false,true,false,false));
    assert(EngineComputesSkill(false,false,false,true,false));
    assert(EngineComputesSkill(false,false,false,false,true));
    assert(EngineComputesSkill(false,true,false,false,false));
    assert(!EngineComputesSkill(false,false,false,false,false));

    // A melee combo completes before the next ordinary spell. Context changes
    // (foe escapes, finisher or valuable Dispel) may interrupt it.
    for(int job=0;job<4;++job) for(int group=1;group<=2;++group) {
        const auto profile=GetProfile(job,group);
        const unsigned minimum=ComboBeforeSkill(profile.style);
        assert(CanBreakCombo(profile.style,0,true,false,false));
        for(unsigned hits=1;hits<minimum;++hits) {
            assert(!CanBreakCombo(profile.style,hits,true,false,false));
            assert(CanBreakCombo(profile.style,hits,false,false,false));
            assert(CanBreakCombo(profile.style,hits,true,true,false));
            assert(CanBreakCombo(profile.style,hits,true,false,true));
        }
        assert(CanBreakCombo(profile.style,minimum,true,false,false));
        const auto normal=BetweenSkills(profile,1100,800,280,false);
        assert(!normal.attack);
        assert(BetweenSkills(profile,normal.approachRange+170,800,280,false).attack);
    }
    assert(ComboBeforeSkill(Style::Body)>ComboBeforeSkill(Style::Mental));
    assert(ComboBeforeSkill(Style::Weapon)>ComboBeforeSkill(Style::Magic));
    assert(ComboBeforeSkill(Style::Archer)==1);
    // Measure interruption from the end of a swing, including a slow two-hand
    // motion and the 32-bit clock wrap, not from its initial packet.
    assert(!ComboTimedOut(2000,4000));
    assert(!ComboTimedOut(5000,4000));
    assert(ComboTimedOut(6300,4000));
    assert(!ComboTimedOut(100,UINT32_MAX-100));
    assert(ComboTimedOut(2400,UINT32_MAX-100));

    SkillSituation direct; direct.level=20;
    SkillSituation expensive=direct; expensive.level=40; expensive.affordable=false;
    for(Style style:{Style::Body,Style::Mental,Style::Dagger,Style::Archer,
                     Style::Weapon,Style::Magic,Style::Dragon,Style::Heal}) {
        assert(SkillScore(style,direct)>SkillScore(style,expensive));
    }
    // Mental chooses useful control, then damage while the foe is already stunned.
    SkillSituation control=direct; control.control=true;
    assert(SkillScore(Style::Mental,control)>SkillScore(Style::Mental,direct));
    control.foeStunned=true;
    assert(SkillScore(Style::Mental,control)<SkillScore(Style::Mental,direct));
    // Dagger chooses Ambush by actual facing, not the stale previous rotation.
    SkillSituation ambush=direct; ambush.backstab=true;
    assert(SkillScore(Style::Dagger,ambush)<SkillScore(Style::Dagger,direct));
    ambush.behind=true;
    assert(SkillScore(Style::Dagger,ambush)>SkillScore(Style::Dagger,direct));
    // Archer/Dagger poison openers lose priority when poison is already running.
    SkillSituation poison=direct; poison.poison=true;poison.opening=true;
    for(Style style:{Style::Archer,Style::Dagger}) {
        assert(SkillScore(style,poison)>SkillScore(style,direct));
        auto running=poison;running.foePoisoned=true;
        assert(SkillScore(style,running)<SkillScore(style,direct));
    }
    // WP utility needs an actual buff; a more powerful but unaffordable Dispel
    // cannot displace an available attack.
    SkillSituation dispel=direct;dispel.dispel=true;
    assert(SkillScore(Style::Weapon,dispel)==-10000);
    dispel.valuableBuff=true;
    assert(SkillScore(Style::Weapon,dispel)>SkillScore(Style::Weapon,direct));
    dispel.affordable=false;
    assert(SkillScore(Style::Weapon,dispel)<SkillScore(Style::Weapon,direct));
    // BM slows a close opponent when useful, uses a burst finisher, and avoids
    // continuously fleeing from its own melee sequence.
    SkillSituation slow=direct;slow.slow=true;slow.close=true;
    assert(SkillScore(Style::Magic,slow)>SkillScore(Style::Magic,direct));
    slow.foeSlowed=true;
    assert(SkillScore(Style::Magic,slow)<SkillScore(Style::Magic,direct));
    SkillSituation burst=direct;burst.burst=true;burst.finisher=true;
    assert(SkillScore(Style::Magic,burst)>SkillScore(Style::Magic,direct));
    assert(!CasterRetreat(80,false));assert(!CasterRetreat(35,true));
    assert(CasterRetreat(15,true));
    // Duel override keeps Dragon Roar around the caster despite the local
    // engine's target-centred extension (the adapter clears GetTarget during cast).
    assert(EffectiveSkillRange(0,900,true,true,false,true)==900);
    assert(EffectiveSkillRange(0,500,true,true,false,false)==500);
    assert(EffectiveSkillRange(0,0,false,true,false,false)==800);
    assert(EffectiveSkillRange(0,500,false,false,true,false)==500);
    assert(EffectiveSkillRange(0,0,false,false,false,false)==300);
    // Healer keeps PE for a learned ready Cure when HP drops; normal attacks
    // remain available while that reserve prevents an offensive cast.
    assert(HasSkillResources(300,120,150));
    assert(!HasSkillResources(220,120,150));
    assert(HasSkillResources(120,120,0));
    assert(!HasSkillResources(80,120,0));
    assert(!HasSkillResources(-1,0,0));
    // Actual WP regression: distance 264 allows sword hits but not Finger's
    // safe cast limit 260. Approach closer, rather than waiting forever at 264.
    assert(BetweenSkills(GetProfile(2,1),264,800,280,false).attack);
    assert(!SkillInRange(264,300,0,false,true,300));
    const int fingerApproach=SkillStandOff(300,200);
    assert(fingerApproach==60);
    assert(SkillInRange(fingerApproach+170,300,0,false,true,300));
    // Never assign a human duellist to a bot's missing sync client. Default
    // contexts and simulated bot victims retain the original ownership path.
    assert(!AssignClientSyncOwner(true,true));
    assert(AssignClientSyncOwner(false,true));
    assert(AssignClientSyncOwner(true,false));
    assert(AssignClientSyncOwner(false,false));
    // The native human melee impact is prepared before the combo packet.
    // Its movement credit replaces (never adds to) the next check's credit;
    // bow hits, PvE, Guild War and bot victims receive none of this override.
    assert(NeedsHitSlideAllowance(true,true,true));
    assert(!NeedsHitSlideAllowance(true,true,false));
    assert(!NeedsHitSlideAllowance(false,true,true));
    assert(!NeedsHitSlideAllowance(true,false,true));
    int credit=0;
    for(int hit=0;hit<1000;++hit) credit=HitSlideMovementBonus(credit);
    assert(credit==hitSlideAllowance);
    assert(HitSlideMovementBonus(1000)==1000);
    // Fast Attack cannot rely on the remote player's client to move the bot.
    assert(FastAttackRange(800)==280);
    assert(FastAttackRange(180)==180);
    assert(!SkillInRange(500,FastAttackRange(800),0,false,false,0));
    assert(!SkillInRange(241,FastAttackRange(800),0,false,false,0));
    assert(SkillInRange(240,FastAttackRange(800),0,false,false,0));
    // Death is two-phase: cleanup must not call battle_end during lethal
    // Stun, which would stand the corpse up and cancel its pending death.
    assert(!CanClearEngineVictim(false,0));
    assert(!CanClearEngineVictim(false,-1));
    assert(CanClearEngineVictim(true,0));
    assert(CanClearEngineVictim(false,1));
    // Native per-target and total-hit budgets both cap the contacts.
    assert(DuelSkillHitCount(3,3,5)==3);
    assert(DuelSkillHitCount(3,3,12)==3);
    assert(DuelSkillHitCount(3,3,1)==1);
    assert(DuelSkillHitCount(3,2,12)==2);
    assert(DuelSkillHitCount(3,3,0)==3);
    SkillHitSequence sequence;
    StartSkillHits(sequence,33,3,1000,1400);
    assert(!ClaimSkillHit(sequence,1249));
    assert(ClaimSkillHit(sequence,1250));
    assert(!ClaimSkillHit(sequence,1250)); // full/light pass cannot double-hit
    assert(ClaimSkillHit(sequence,1500));
    assert(ClaimSkillHit(sequence,1750));
    assert(sequence.remaining==0 && sequence.attempted==3);
    assert(!ClaimSkillHit(sequence,2000));
    // A miss consumes its motion contact too; it is never banked for later.
    StartSkillHits(sequence,1,3,0,1400);
    int landed=0;
    for(unsigned tick=250;tick<=1000;tick+=250) {
        if(ClaimSkillHit(sequence,tick) && SkillInRange(tick==500?500:100,300,0,false,false,0)) ++landed;
    }
    assert(landed==2 && sequence.attempted==3);
    StartSkillHits(sequence,1,3,0,1400);
    assert(ClaimSkillHit(sequence,1000));
    assert(!ClaimSkillHit(sequence,1000)); // no instant overdue burst
    assert(!ClaimSkillHit(sequence,1400) && !sequence.remaining);
    StartSkillHits(sequence,1,3,UINT32_MAX-100,1400);
    assert(!ClaimSkillHit(sequence,148));
    assert(ClaimSkillHit(sequence,149));
    int before=0,opening=0,none=0,ready=0;
    for(int roll=0;roll<100;++roll) {
        switch(DaggerStealthPlan(roll)) {
            case StealthPlan::Before:++before;break;
            case StealthPlan::Opening:++opening;break;
            case StealthPlan::None:++none;break;
        }
        if(std::string(ReadyPrompt(roll))=="r?") ++ready;
    }
    assert(before==35 && opening==40 && none==25 && ready==85);
    // Renewing a buff under ranged fire is unsafe even at a large distance.
    assert(SafeBuffCast(80,900,false));
    assert(!SafeBuffCast(80,900,false,true));
    assert(!SafeBuffCast(80,200,false));
    assert(SafeBuffCast(80,200,true,true));
    assert(!SafeBuffCast(40,900,true));

    // New duels must not inherit the previous foe's observations or combo.
    playerbot_pvp::NoteDuelStarted(22,11,10000);
    auto& old=playerbot_pvp::duels.at(22);
    old.weaponChain=3;old.opponentBuff=true;old.lastDamagedAt=99;old.stealthOpening=true;old.skillHits=sequence;
    playerbot_pvp::NoteDuelStarted(22,33,20000);
    const auto& fresh=playerbot_pvp::duels.at(22);
    assert(fresh.weaponChain==0 && !fresh.opponentBuff && fresh.lastDamagedAt==0 && !fresh.stealthOpening);
    assert(fresh.opponentPid==33);
    assert(fresh.skillHits.remaining==0 && fresh.skillHits.skill==0);
    std::cout<<"all eight duel tactic profiles and execution contracts passed\n";
}
