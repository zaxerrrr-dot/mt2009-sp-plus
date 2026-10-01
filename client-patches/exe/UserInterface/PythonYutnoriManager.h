/**
* MT2009_PLUS_MINIGAMES_V1: Yut Nori 3D thrower (race 20505) drawn into a render target.
* After Owsap v6.2.6 PythonYutnoriManager (author blackdragonx61 / Mali).
**/

#pragma once

#if defined(ENABLE_MINI_GAME_YUTNORI)
#include "InstanceBase.h"

class CPythonYutnoriManager : public CSingleton<CPythonYutnoriManager>
{
public:
	enum
	{
		YUTNORI_MODEL_RACE = 20505,
	};

	CPythonYutnoriManager();
	virtual ~CPythonYutnoriManager();

	void Initialize();
	void Destroy();

	bool Create(DWORD dwWidth, DWORD dwHeight);
	void Reset() const;

	bool CreateModelInstance();
	void SelectModel() const;
	void UpdateModel();
	void DeformModel() const;
	void RenderModel() const;

	bool ChangeMotion(DWORD dwMotionIndex);
	void NotifyMotionDone() const;
	void SetShow(bool bShow);

private:
	std::vector<DWORD> m_MotionVec;
	CInstanceBase* m_pModelInstance;
	bool m_bShow;
	bool m_bMotionProcess;
	bool m_bMotionDoneProcess;
	float m_fAlpha;
	float m_fColorAlpha;
	D3DXCOLOR m_dColor;
};
#endif
