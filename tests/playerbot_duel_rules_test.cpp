#include "../linux-port/overlays/playerbot/src/game/src/playerbot_pvp_policy.h"
#include <cassert>
#include <iostream>
int main() {
    using namespace playerbot_duel;
    // Regression: every build must reach an ordinary weapon attack while its
    // skills cool down or it lacks SP, even when starting at its preferred range.
    for(int job=0;job<4;++job) for(int group=1;group<=2;++group) {
        const auto profile=GetProfile(job,group);
        const auto distant=BetweenSkills(profile,profile.startRange,800,280,false);
        assert(!distant.attack); // Start ranges exceed ordinary weapon reach.
        assert(distant.approachRange<distant.reach);
        // Navigation stops up to 100 units early and snaps to 50-unit cells.
        // Even that worst-case endpoint must permit a hit, rather than a loop
        // of successful 'arrivals' beyond melee reach.
        assert(BetweenSkills(profile,distant.approachRange+170,800,280,false).attack);
        const auto arrived=BetweenSkills(profile,distant.approachRange,800,280,false);
        assert(arrived.attack);
        assert(BetweenSkills(profile,distant.reach,800,280,false).attack);
        assert(!BetweenSkills(profile,distant.reach+1,800,280,false).attack);
        const bool caster=profile.style==Style::Magic || profile.style==Style::Dragon || profile.style==Style::Heal;
        if(caster) {
            assert(!arrived.reposition); // No kite away from the required melee hit.
            assert(BetweenSkills(profile,130,800,280,true).reposition);
        }
        if(profile.style==Style::Archer) {
            assert(distant.reach==800 && distant.approachRange==600);
            assert(BetweenSkills(profile,700,800,280,false).attack);
            assert(distant.reposition); // Bow shots retain the ranged tactical profile.
        } else assert(distant.reach==280 && distant.approachRange==80);
    }
    assert(!CasterRetreat(80,false));
    assert(!CasterRetreat(40,false));
    assert(CasterRetreat(35,false));
    assert(!CasterRetreat(35,true));
    // The same start area applies to all eight classes, regardless of ideal range.
    for(int job=0;job<4;++job) for(int group=1;group<=2;++group) {
        const auto profile=GetProfile(job,group);
        for(int distance:{0,100,profile.startRange,1000,1200,1800})
            assert(!NeedsPreparationApproach(distance));
        assert(NeedsPreparationApproach(1801));
    }
    // Snapshot of offensive proto ranges for ALL eight builds (world v2.25.0).
    // Skill, target, splash, self-only, melee, expected conservative cast limit.
    struct SkillCase { int id,target,splash; bool self,melee; int limit; };
    const SkillCase skills[]={
        {1,0,0,false,true,260},{2,0,200,false,true,260},{5,0,200,false,true,260},
        {16,0,100,false,true,260},{17,0,200,false,true,260},{18,0,400,true,true,360},{20,1200,200,false,true,1160},
        {31,0,0,false,true,260},{33,0,0,false,true,260},{32,800,0,false,true,760},{35,800,200,false,false,760},
        {46,2500,0,false,false,2460},{47,0,500,false,false,460},{48,2500,300,false,false,2460},{50,2500,300,false,false,2460},
        {61,0,0,false,true,260},{62,0,500,true,true,460},{66,1800,200,false,false,1760},
        {77,0,500,true,false,460},{76,1500,200,false,false,1460},{80,1200,400,false,false,1160},{81,1500,200,false,false,1460},
        {92,0,0,false,false,760},{93,0,900,true,false,860},{91,1800,201,false,false,1760},
        {106,1800,200,false,false,1760},{108,2500,0,false,false,2460},{107,1500,400,false,false,1460}
    };
    for(const auto& skill:skills) {
        const bool magic=skill.id==35 || skill.id==66 || (skill.id>=76 && skill.id<=81) || skill.id>=91;
        const bool arrow=skill.id>=46 && skill.id<=50;
        const int range=EffectiveSkillRange(skill.target,skill.splash,skill.self,magic,arrow,skill.id==93);
        assert(SkillInRange(skill.limit,range,0,false,false,300));
        assert(!SkillInRange(skill.limit+1,range,0,false,false,300));
    }
    // Actual world.skill_proto: Dragon Swirl is SELFONLY/melee, splash=500.
    assert(SkillInRange(400,0,500,true,true,300));
    assert(SkillInRange(250,0,500,true,true,300));
    assert(!SkillInRange(461,0,500,true,true,300));
    // Zero target range is not unlimited reach (Finger Strike/rolling dagger).
    assert(!SkillInRange(700,0,0,false,true,300));
    assert(SkillInRange(170,0,0,false,true,300));
    // Explicit ranged melee skills retain their proto range.
    assert(SkillInRange(700,800,0,false,true,300));
    assert(!SkillInRange(780,800,0,false,true,300));
    assert(SkillInRange(1400,1500,200,false,false,300));
    assert(!SkillInRange(1500,1500,200,false,false,300));
    assert(!SkillInRange(0,0,0,true,false,300));
    for(const char* s:{"g","G","go","GO","Go"," ready ","\tREADY\n"}) assert(ReadyText(s));
    for(const char* s:{"","gg","go now","g!","guild g","ready?"}) assert(!ReadyText(s));
    assert(!ReadyText(nullptr));
    assert(BlockHP(true,false));assert(!BlockHP(true,true));
    assert(!BlockHP(false,false));assert(!BlockHP(false,true));
    for(int tier=0;tier<4;++tier) {
        assert(!Spend(Reserve(tier),tier,3,1000));
        assert(!Spend(Reserve(tier)-1,tier,3,1000));
        if(tier<3) {
            assert(Spend(Reserve(tier)+1,tier,tier+1,Cost(tier)));
            assert(!Spend(Reserve(tier)+1,tier,tier+1,Cost(tier)-1));
            assert(!Spend(100,tier,tier,100));
        } else assert(!Spend(10000,tier,3,10000));
    }
    assert(Threat(80,60,0)==0);assert(Threat(80,80,0)==1);
    assert(Threat(80,90,0)==2);assert(Threat(80,100,0)==3);
    assert(Threat(80,80,2)==3);
    for(int job=0;job<4;++job) for(int group=1;group<=2;++group) {
        auto p=GetProfile(job,group);assert(p.range>0 && p.startRange>=300);
        assert(p.style!=GetProfile(job,3-group).style);
    }
    assert(GetProfile(0,1).minimum==0);assert(GetProfile(1,2).minimum>=500);
    assert(GetProfile(3,2).minimum>GetProfile(3,1).minimum);
    using namespace playerbot_pvp;
    challenges.clear();duels.clear();history.clear();
    NoteChallenge(11,22);NoteChallenge(33,22);assert(challenges.at(22).challengerPid==11);
    uint32_t pid=0,seen=0;assert(PeekChallenge(22,pid,seen,100));assert(pid==11 && seen==100);
    assert(!NoteReady(22,33));assert(!challenges.at(22).playerReady);
    assert(NoteReady(22,11));
    assert(PeekChallenge(22,pid,seen,150));assert(seen==100 && challenges.at(22).playerReady);
    assert(!PreparationExpired(challenges.at(22),100+prepareTimeout));
    assert(PreparationExpired(challenges.at(22),101+prepareTimeout));
    challenges.at(22).readyAt=1000;
    assert(!PreparationExpired(challenges.at(22),1000+readyTimeout));
    assert(PreparationExpired(challenges.at(22),1001+readyTimeout));
    challenges.at(22).readyAt=UINT32_MAX-100;
    assert(!PreparationExpired(challenges.at(22),100));
    assert(PreparationExpired(challenges.at(22),readyTimeout+100));
    Forget(22);assert(!PeekChallenge(22,pid,seen,200));
    NoteChallenge(33,22);assert(!challenges.at(22).playerReady);Forget(22);
    NoteDuelStarted(22,11,1000);assert(IsInDuel(22,999));assert(GetDuelOpponent(22,999)==11);
    assert(!IsInDuel(22,1000));assert(duels.empty());
    NoteDuelStarted(22,11,1000);duels.at(22).prepared=true;
    assert(!IsInDuel(22,1000));assert(duels.count(22)==1);EndDuel(22);
    assert(DuelStands(200,UINT32_MAX-100));assert(!DuelStands(UINT32_MAX-100,200));
    NoteDuelStarted(22,11,200);assert(IsInDuel(22,UINT32_MAX-100));EndDuel(22);
    RecordResult(22,11,-1);RecordResult(22,11,-1);assert(history.at({22,11}).streak==2);
    RecordResult(22,11,1);assert(history.at({22,11}).streak==0);
    assert(history.at({22,11}).wins==1 && history.at({22,11}).losses==2);
    for(unsigned i=0;i<3000;++i)RecordResult(100+i,77,0);
    assert(history.size()==2048);
    std::cout<<"duel rules and lifecycle tests passed\n";
}
