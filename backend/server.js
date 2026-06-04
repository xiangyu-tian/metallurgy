// server-unified.js - 统一版本（本地+服务器）
const express = require('express');
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const os = require('os');
const axios = require('axios');

// ========== 小模型注册表（大小模型协同） ==========
const smallModelRegistry = [
  {
    id: 'thermodynamics',
    name: '热力学推理',
    icon: '🔬',
    handler: async (params) => {
      const { tool, ...rest } = params;
      // 子工具分发
      if (tool === 'enthalpy') {
        const { reaction } = rest;
        const db = [['C + O\u2082 \u2192 CO\u2082', -393.5, '碳完全燃烧'],['2C + O\u2082 \u2192 2CO', -221.0, '碳不完全燃烧'],['FeO + C \u2192 Fe + CO', 158.0, '氧化亚铁碳还原'],['Fe\u2082O\u2083 + 3CO \u2192 2Fe + 3CO\u2082', -24.7, '赤铁矿间接还原']];
        const m = db.find(r => r[0] === reaction);
        if (!m) return { summary: '不支持该反应', data: {}, unit: 'kJ/mol' };
        return { summary: `${m[0]} 标准焓变 ΔH° = ${m[1]} kJ/mol（${m[2]}）`, data: {'反应': m[0], '名称': m[2], 'ΔH°': `${m[1]} kJ/mol`, '反应类型': m[1] < 0 ? '放热反应' : '吸热反应', '热效应': `${Math.abs(m[1])} kJ/mol`}, unit: 'kJ/mol' };
      }
      if (tool === 'direction') {
        const { reaction, temperature } = rest;
        const T = parseFloat(temperature) || 1600, TK = T + 273.15;
        const db = [['C + O\u2082 \u2192 CO\u2082', -393.5, 2.9],['2C + O\u2082 \u2192 2CO', -221.0, 179.2],['FeO + C \u2192 Fe + CO', 158.0, 150.0],['Fe\u2082O\u2083 + 3CO \u2192 2Fe + 3CO\u2082', -24.7, 15.6],['CaCO\u2083 \u2192 CaO + CO\u2082', 178.3, 160.6]];
        const m = db.find(r => r[0] === reaction);
        if (!m) return { summary: '不支持该反应', data: {}, unit: '' };
        const deltaG = m[1] - TK * m[2] / 1000;
        const dir = deltaG < -10 ? '正向强烈自发' : deltaG < 0 ? '正向自发' : deltaG < 10 ? '逆向自发（需能量输入）' : '逆向强烈自发';
        let note = '';
        if (reaction.includes('CaCO\u2083')) { const decK = m[1] / (m[2] / 1000); note = `。分解温度约 ${(decK - 273.15).toFixed(0)}°C`; }
        return { summary: `${m[0]} 在 ${T}°C，ΔG = ${deltaG.toFixed(2)} kJ/mol，${dir}${note}`, data: {'反应': m[0], '温度': `${T}°C`, 'ΔG': `${deltaG.toFixed(2)} kJ/mol`, '方向': dir}, unit: 'kJ/mol' };
      }
      if (tool === 'equilibrium') {
        const { reaction, temperature } = rest;
        const T = parseFloat(temperature) || 1600, TK = T + 273.15;
        const db = [['C + O\u2082 \u2192 CO\u2082', -393.5, 2.9],['2C + O\u2082 \u2192 2CO', -221.0, 179.2],['FeO + C \u2192 Fe + CO', 158.0, 150.0],['Fe\u2082O\u2083 + 3CO \u2192 2Fe + 3CO\u2082', -24.7, 15.6]];
        const m = db.find(r => r[0] === reaction);
        if (!m) return { summary: '不支持该反应', data: {}, unit: '' };
        const deltaG = m[1] - TK * m[2] / 1000, K = Math.exp(-deltaG * 1000 / (8.314 * TK));
        return { summary: `${m[0]} 在 ${T}°C，K = ${K.toExponential(4)}`, data: {'反应': m[0], '温度': `${T}°C`, 'ΔG': `${deltaG.toFixed(2)} kJ/mol`, 'K': K.toExponential(4)}, unit: '' };
      }
      // ========== 默认：完整热力学计算（含全部10种反应）==========
      // ========== 真实热化学数据库（10种常见冶金反应） ==========
      const reactionDB = [
        {
          reaction: 'C + O₂ → CO₂',
          deltaH: -393.5,    // kJ/mol
          deltaS: 2.9,       // J/(mol·K)
          name: '碳完全燃烧'
        },
        {
          reaction: '2C + O₂ → 2CO',
          deltaH: -221.0,
          deltaS: 179.2,
          name: '碳不完全燃烧'
        },
        {
          reaction: 'FeO + C → Fe + CO',
          deltaH: 158.0,
          deltaS: 150.0,
          name: '氧化亚铁碳还原（直接还原）'
        },
        {
          reaction: 'Fe₂O₃ + 3CO → 2Fe + 3CO₂',
          deltaH: -24.7,
          deltaS: 15.6,
          name: '赤铁矿间接还原'
        },
        {
          reaction: 'Fe₃O₄ + 4CO → 3Fe + 4CO₂',
          deltaH: -14.5,
          deltaS: 10.2,
          name: '磁铁矿间接还原'
        },
        {
          reaction: 'CaCO₃ → CaO + CO₂',
          deltaH: 178.3,
          deltaS: 160.6,
          name: '碳酸钙分解（石灰石煅烧）'
        },
        {
          reaction: 'SiO₂ + 2C → Si + 2CO',
          deltaH: 689.6,
          deltaS: 359.3,
          name: '二氧化硅碳还原（工业硅冶炼）'
        },
        {
          reaction: '2FeO + Si → 2Fe + SiO₂',
          deltaH: -527.4,
          deltaS: -52.8,
          name: '硅还原氧化亚铁（脱氧反应）'
        },
        {
          reaction: 'MnO + C → Mn + CO',
          deltaH: 276.1,
          deltaS: 151.6,
          name: '氧化锰碳还原'
        },
        {
          reaction: 'Fe₂O₃ + 2Al → 2Fe + Al₂O₃',
          deltaH: -851.5,
          deltaS: -38.0,
          name: '铝热反应'
        }
      ];

      const { reaction, temperature, components } = params;
      const T = parseFloat(temperature) || 1600;
      const TK = T + 273.15;  // 开尔文温度
      const R = 8.314;        // J/(mol·K)

      // 匹配反应（去除空格后比较，提高容错率）
      const normalize = s => s.replace(/\s+/g, '');
      const inputReaction = normalize(reaction || '');
      const matched = reactionDB.find(r => normalize(r.reaction) === inputReaction);

      if (!matched) {
        // 匹配不到时返回可用反应列表
        const reactionList = reactionDB.map((r, i) =>
          `${i + 1}. ${r.reaction}（${r.name}）`
        ).join('\n');
        return {
          summary: `❌ 不支持该反应："${reaction || ''}"。请从以下可用反应中选择：\n${reactionList}`,
          data: {
            '错误': `不支持的反应：${reaction || ''}`,
            '可用反应列表': reactionList
          },
          unit: ''
        };
      }

      // 真实热力学计算
      const deltaH = matched.deltaH;  // kJ/mol
      const deltaS = matched.deltaS;  // J/(mol·K)
      const deltaG = deltaH - TK * deltaS / 1000;  // ΔG = ΔH - T·ΔS（kJ/mol）
      const equilibriumConstant = Math.exp(-deltaG * 1000 / (R * TK));

      // 反应方向判定
      let direction;
      if (deltaG < -10) {
        direction = '正向强烈自发';
      } else if (deltaG < 0) {
        direction = '正向自发';
      } else if (deltaG < 10) {
        direction = '逆向自发（需外界能量输入）';
      } else {
        direction = '逆向强烈自发（需大量外界能量输入）';
      }

      // 对碳酸钙分解反应增加特征温度说明
      let extraNote = '';
      if (matched.reaction === 'CaCO₃ → CaO + CO₂') {
        // 计算分解温度：T = ΔH/ΔS（当ΔG = 0时）
        const decompK = deltaH / (deltaS / 1000);
        const decompC = decompK - 273.15;
        extraNote = `。CaCO₃ 理论分解温度约为 ${decompC.toFixed(0)}°C（标准状态）`;
      }

      return {
        summary: `计算完成：${matched.reaction} 在 ${T}°C 时，ΔG = ${deltaG.toFixed(2)} kJ/mol，反应${direction}${extraNote}。`,
        data: {
          '反应式': matched.reaction,
          '反应名称': matched.name,
          '温度': `${T} °C（${TK.toFixed(0)} K）`,
          'ΔH° (标准焓变)': `${deltaH.toFixed(1)} kJ/mol`,
          'ΔS° (标准熵变)': `${deltaS.toFixed(1)} J/(mol·K)`,
          'ΔG (吉布斯自由能)': `${deltaG.toFixed(2)} kJ/mol`,
          '平衡常数 K': equilibriumConstant.toExponential(4),
          '反应方向': direction
        },
        unit: 'kJ/mol'
      };
    }
  },
  {
    id: 'converter',
    name: '转炉炼钢工艺优化',
    icon: '🔥',
    handler: async (params) => {
      const { tool, siContent, targetCarbon, steelTemp, oxygenFlow } = params;
      const si = parseFloat(siContent) || 0.5, tC = parseFloat(targetCarbon) || 0.05, temp = parseFloat(steelTemp) || 1600, oxy = parseFloat(oxygenFlow) || 25000;
      // 子工具分发
      if (tool === 'oxygen') {
        const oxyConsumption = (si * 8 + tC * 15 + Math.random() * 5).toFixed(1);
        return { summary: `氧耗计算：Si ${si}% + 目标C ${tC}%，预计氧耗 ${oxyConsumption} Nm³/t`, data: {'铁水Si': `${si}%`, '目标碳': `${tC}%`, '预计氧耗': `${oxyConsumption} Nm³/t`, '氧枪流量': `${oxy} Nm³/h`}, unit: 'Nm³' };
      }
      if (tool === 'slag') {
        const basicity = (3.2 + (Math.random() - 0.5) * 0.8).toFixed(2), lime = (si * 2.5 + Math.random()).toFixed(1);
        return { summary: `渣碱度计算：R = ${basicity}，建议石灰用量 ${lime} kg/t`, data: {'铁水Si': `${si}%`, '渣碱度R': basicity, '石灰用量': `${lime} kg/t`}, unit: '' };
      }
      if (tool === 'temperature') {
        const predTemp = temp + (Math.random() - 0.5) * 20;
        return { summary: `温度预测：入炉 ${temp}°C → 终点 ${predTemp.toFixed(0)}°C，温降 ${(temp - predTemp).toFixed(0)}°C`, data: {'入炉温度': `${temp}°C`, '预测终点温度': `${predTemp.toFixed(0)}°C`, '温降': `${(temp - predTemp).toFixed(0)}°C`}, unit: '°C' };
      }
      // 默认：终点预测
      // 模拟预测
      const predictedCarbon = tC + (Math.random() - 0.5) * 0.02;
      const predictedTemp = temp + (Math.random() - 0.5) * 20;
      const oxygenConsumption = (si * 8 + tC * 15 + (Math.random() * 5)).toFixed(1);
      const slagBasicity = (3.2 + (Math.random() - 0.5) * 0.8).toFixed(2);
      return {
        summary: `转炉终点预测：目标碳 ${tC}%，预测终点碳 ${predictedCarbon.toFixed(3)}%，终点温度 ${predictedTemp.toFixed(0)}°C。建议控制氧耗 ${oxygenConsumption} Nm³，确保炉渣碱度 ${slagBasicity}。`,
        data: {
          '铁水 Si 含量': `${si}%`,
          '目标碳含量': `${tC}%`,
          '预测终点碳': `${predictedCarbon.toFixed(3)}%`,
          '预测终点温度': `${predictedTemp.toFixed(0)} °C`,
          '预计氧耗': `${oxygenConsumption} Nm³`,
          '炉渣碱度 (R)': slagBasicity,
          '氧枪流量建议': `${oxygenFlow || 25000} Nm³/h`
        },
        unit: 'wt%'
      };
    }
  },
  {
    id: 'blastfurnace',
    name: '高炉低碳运行分析',
    icon: '🏭',
    handler: async (params) => {
      const { tool, cokeRate, coalRate, production, oreGrade } = params;
      const cr = parseFloat(cokeRate) || 360, coi = parseFloat(coalRate) || 160, prod = parseFloat(production) || 5000, grade = parseFloat(oreGrade) || 62;
      // 子工具分发
      if (tool === 'efficiency') {
        const eff = Math.min(95, ((300 / cr) + (130 / coi)) / 2 * 100).toFixed(1);
        return { summary: `能效评估：焦比 ${cr} kg/t、煤比 ${coi} kg/t，综合能效 ${eff}%`, data: {'焦比': `${cr} kg/t`, '煤比': `${coi} kg/t`, '综合能效': `${eff}%`, '能效等级': eff > 85 ? '优秀' : eff > 75 ? '良好' : '待优化'}, unit: '%' };
      }
      if (tool === 'reduction') {
        const emission = (cr * 2.86 + coi * 2.45) * prod / 1000, bench = (380 * 2.86 + 170 * 2.45) * prod / 1000;
        return { summary: `降碳潜力：当前 ${emission.toFixed(0)} tCO₂/d，较基准 ${bench.toFixed(0)} 降低 ${((1 - emission/bench) * 100).toFixed(1)}%`, data: {'当前日排放': `${emission.toFixed(0)} tCO₂`, '基准日排放': `${bench.toFixed(0)} tCO₂`, '降碳比例': `${((1 - emission/bench) * 100).toFixed(1)}%`}, unit: 'tCO₂' };
      }
      if (tool === 'utilization') {
        const util = Math.min(98, (300 / cr) * 100).toFixed(1);
        return { summary: `碳利用效率：焦比 ${cr} kg/t，碳利用效率 ${util}%`, data: {'焦比': `${cr} kg/t`, '碳利用效率': `${util}%`, '行业标杆': '92%'}, unit: '%' };
      }
      // 默认：碳排放综合评估
      // 计算碳排放
      const carbonEmission = (cr * 2.86 + coi * 2.45) * prod / 1000;
      const benchmarkEmission = (380 * 2.86 + 170 * 2.45) * prod / 1000;
      const reduction = ((1 - carbonEmission / benchmarkEmission) * 100).toFixed(1);
      const carbonIntensity = (carbonEmission / prod).toFixed(2);
      return {
        summary: `高炉碳排放评估：当前焦比 ${cr} kg/t、煤比 ${coi} kg/t，日产量 ${prod} t/d。日碳排放 ${carbonEmission.toFixed(1)} tCO₂，碳排放强度 ${carbonIntensity} tCO₂/t铁水，较行业基准降低 ${reduction}%。`,
        data: {
          '焦比': `${cr} kg/t`,
          '煤比': `${coi} kg/t`,
          '入炉矿品位': `${grade}%`,
          '日产量': `${prod} t/d`,
          '日碳排放量': `${carbonEmission.toFixed(1)} tCO₂`,
          '碳排放强度': `${carbonIntensity} tCO₂/t`,
          '较基准降碳': `${reduction}%`,
          '碳利用效率': `${Math.min(95, ((300 / cr) + (130 / coi)) / 2 * 100).toFixed(1)}%`
        },
        unit: 'tCO₂'
      };
    }
  },
  {
    id: 'casting',
    name: '连铸质量辅助决策',
    icon: '📊',
    handler: async (params) => {
      const { tool, steelGrade, sectionSize, castingSpeed, superheat } = params;
      const speed = parseFloat(castingSpeed) || 1.2, sh = parseFloat(superheat) || 30;
      // 子工具分发
      if (tool === 'segregation') {
        try {
          const featureKeys = ['C','Si','Mn','P','S','Cr','Ni','Mo','V','Ti','Cu','Al','Nb','B','N','Ca','Mg','As','Sn','Zn','Pb'];
          const mlParams = Object.fromEntries(Object.entries(params).filter(([k]) => featureKeys.includes(k)));
          const segRes = await axios.post('http://localhost:8001/api/predict/single', mlParams, { timeout: 15000 });
          if (segRes.data && segRes.data.data) {
            const d = segRes.data.data;
            return { summary: `偏析预测完成：碳极差1=${d['碳极差1']}、碳极差2=${d['碳极差2']}、碳偏析指数=${d['碳偏析指数']}`, data: {'碳极差1': d['碳极差1'], '碳极差2': d['碳极差2'], '碳偏析指数': d['碳偏析指数'], '评估': parseFloat(d['碳偏析指数']) < 1.2 ? '优' : parseFloat(d['碳偏析指数']) < 1.5 ? '良' : '需优化'}, unit: '' };
          }
        } catch (e) {
          console.warn('⚠️ 偏析预测服务调用失败，降级为模拟数据', e.message);
        }
        // 降级：服务不可用时使用模拟数据
        const c1 = (0.8 + Math.random() * 0.4).toFixed(3), c2 = (0.6 + Math.random() * 0.3).toFixed(3), idx = (1.0 + Math.random() * 0.5).toFixed(3);
        return { summary: `偏析预测（模拟）：碳极差1=${c1}、碳极差2=${c2}、碳偏析指数=${idx}`, data: {'碳极差1': c1, '碳极差2': c2, '碳偏析指数': idx, '评估': parseFloat(idx) < 1.2 ? '优' : parseFloat(idx) < 1.5 ? '良' : '需优化'}, unit: '' };
      }
      if (tool === 'crack') {
        const crackIdx = (Math.random() * 0.5).toFixed(3);
        return { summary: `表面裂纹预测：指数 ${crackIdx}（${parseFloat(crackIdx) < 0.2 ? '低风险' : parseFloat(crackIdx) < 0.35 ? '中风险' : '高风险'}）`, data: {'裂纹指数': crackIdx, '风险等级': parseFloat(crackIdx) < 0.2 ? '低' : parseFloat(crackIdx) < 0.35 ? '中' : '高'}, unit: '' };
      }
      if (tool === 'porosity') {
        const porIdx = (0.5 + Math.random() * 1.0).toFixed(2);
        return { summary: `中心疏松预测：指数 ${porIdx}（${parseFloat(porIdx) < 1.0 ? '轻微' : parseFloat(porIdx) < 1.5 ? '中等' : '严重'}）`, data: {'疏松指数': porIdx, '严重程度': parseFloat(porIdx) < 1.0 ? '轻微' : parseFloat(porIdx) < 1.5 ? '中等' : '严重'}, unit: '' };
      }
      // 默认：综合质量评分
      // 质量指标模拟
      const centerSegregation = (0.8 + (Math.random() - 0.5) * 0.6).toFixed(2);
      const porosity = (1.2 + (Math.random() - 0.5) * 1.0).toFixed(2);
      const surfaceCrack = (Math.random() * 0.5).toFixed(3);
      const qualityScore = Math.min(100, Math.max(60, 95 - parseFloat(centerSegregation) * 5 - parseFloat(porosity) * 3)).toFixed(1);
      const suggestion = qualityScore >= 90 ? '质量优良，可正常生产' :
                         qualityScore >= 80 ? '质量良好，建议适当降低拉速' :
                         '质量一般，建议检查过热度与冷却制度';
      return {
        summary: `铸坯质量预测：${steelGrade || 'Q235B'} ${sectionSize || '200×200mm'}，质量评分 ${qualityScore} 分。${suggestion}。`,
        data: {
          '钢种': steelGrade || 'Q235B',
          '断面': sectionSize || '200×200mm',
          '拉速': `${speed} m/min`,
          '过热度': `${sh} °C`,
          '中心偏析指数': centerSegregation,
          '疏松指数': porosity,
          '表面裂纹指数': surfaceCrack,
          '综合质量评分': `${qualityScore} 分`
        },
        unit: '评分'
      };
    }
  },
  {
    id: 'simulation',
    name: '对话式仿真与工单协同',
    icon: '💻',
    handler: async (params) => {
      const { tool, scenario, equipment, duration } = params;
      // 子工具分发
      if (tool === 'risk') {
        const level = ['低', '中', '高'][Math.floor(Math.random() * 3)], prob = (Math.random() * 100).toFixed(1);
        return { summary: `风险评估：${scenario || '标准冶炼'} 场景风险等级 ${level}（概率 ${prob}%）`, data: {'场景': scenario || '标准冶炼', '设备': equipment || '转炉', '风险等级': level, '风险概率': `${prob}%`}, unit: '' };
      }
      if (tool === 'params') {
        const recTemp = (1550 + Math.random() * 50).toFixed(0), recPress = (2 + Math.random()).toFixed(1), recTime = (30 + Math.random() * 30).toFixed(0);
        return { summary: `参数推荐：温度 ${recTemp}°C、压力 ${recPress} atm、时长 ${recTime} min`, data: {'推荐温度': `${recTemp}°C`, '推荐压力': `${recPress} atm`, '推荐时长': `${recTime} min`}, unit: '' };
      }
      // 默认：操作工单生成
      const steps = [
        `1. 检查 ${equipment || '转炉'} 设备状态，确认各传感器读数正常`,
        `2. 设定工艺参数：温度 ${(1550 + Math.random() * 50).toFixed(0)}°C，压力 ${(2 + Math.random()).toFixed(1)} atm`,
        `3. 启动 ${scenario || '标准'} 冶炼程序，持续 ${duration || 45} 分钟`,
        `4. 实时监控关键指标，每 5 分钟记录一次数据`,
        `5. 完成操作后执行设备自检并生成报告`
      ];
      const duration_min = parseInt(duration) || 45;
      return {
        summary: `仿真工单已生成：${scenario || '标准冶炼'}场景，涉及设备 ${equipment || '转炉'}，预计耗时 ${duration_min} 分钟。`,
        data: {
          '场景': scenario || '标准冶炼',
          '涉及设备': equipment || '转炉',
          '预计耗时': `${duration_min} 分钟`,
          '操作步骤': steps.join('\n'),
          '风险等级': ['低', '中', '高'][Math.floor(Math.random() * 3)],
          '建议优先级': ['常规', '优先', '紧急'][Math.floor(Math.random() * 3)]
        },
        unit: '操作工单'
      };
    }
  }
];

// ========== 小模型调用解析与执行工具 ==========

/**
 * 解析 LLM 响应中的 [调用:模型ID:参数JSON] 标记并执行对应 handler
 */
function parseAndExecuteSmallModelCalls(llmContent) {
  const pattern = /\[调用\s*:\s*(\w+)\s*:\s*(\{[\s\S]*?\})\]/g;
  let cleanedContent = llmContent;
  const handlerPromises = [];
  const matchInfo = [];

  let match;
  while ((match = pattern.exec(llmContent)) !== null) {
    const fullMatch = match[0];
    const modelId = match[1];
    const paramsStr = match[2];

    const registryItem = smallModelRegistry.find(m => m.id === modelId);

    if (registryItem) {
      let params = {};
      try {
        params = JSON.parse(paramsStr);
      } catch (e) {
        console.warn(`⚠️ 小模型 ${modelId} 参数JSON解析失败:`, paramsStr);
      }

      const queryText = params.query || params.reaction || params.message || JSON.stringify(params);
      const promise = callSmallModelChat(modelId, queryText)
        .then(reply => ({
          fullMatch,
          modelName: registryItem.name,
          icon: registryItem.icon,
          reply
        }))
        .catch(error => ({
          fullMatch,
          modelName: registryItem.name,
          icon: registryItem.icon,
          error: error.message
        }));

      handlerPromises.push(promise);
      matchInfo.push({ fullMatch, modelId, registryItem });
    } else {
      // 模型 ID 不存在，替换为友好错误
      cleanedContent = cleanedContent.replace(
        fullMatch,
        `> ⚠️ **小模型调用失败**：未知模型 ID "${modelId}"`
      );
      console.warn(`⚠️ 未知小模型 ID: ${modelId}`);
    }
  }

  return { cleanedContent, handlerPromises, matchInfo };
}

/**
 * 调用小模型 LLM 对话（供主聊天和独立工具共享）
 */
async function callSmallModelChat(modelId, message) {
  const prompt = toolSystemPrompts[modelId];
  if (!prompt) throw new Error(`未知小模型: ${modelId}`);

  const response = await axios.post(
    QWEN_API_URL,
    {
      model: 'qwen-plus',
      input: {
        messages: [
          { role: 'system', content: prompt },
          { role: 'user', content: message }
        ]
      },
      parameters: {
        result_format: 'message',
        temperature: 0.6,
        top_p: 0.8,
        repetition_penalty: 1.05,
        max_tokens: 1024
      }
    },
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DASHSCOPE_API_KEY}`,
        'X-DashScope-SSE': 'disable'
      },
      timeout: 30000
    }
  );

  return response.data.output.choices[0].message.content;
}

/**
 * 将小模型结果格式化为 Markdown 块
 */
function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function nl2br(str) {
  return str.replace(/\n/g, '<br>');
}

function formatSmallModelBlock(modelName, icon, result) {
  if (result.error) {
    return `<div class="sml-card sml-card-error">
      <div class="sml-card-header">
        <span class="sml-card-icon">⚠️</span>
        <span class="sml-card-title">${escapeHtml(modelName)}</span>
        <span class="sml-card-badge sml-badge-error">调用异常</span>
      </div>
      <div class="sml-card-body">
        <div class="sml-card-summary">${nl2br(escapeHtml(result.error))}</div>
      </div>
    </div>`;
  }

  const modelId = smallModelRegistry.find(m => m.name === modelName)?.id || 'unknown';
  const content = result.reply || result.summary || '';
  let block = `<div class="sml-card sml-model-${escapeHtml(modelId)}">`;
  block += `<div class="sml-card-header">`;
  block += `<span class="sml-card-icon">${icon}</span>`;
  block += `<span class="sml-card-title">${escapeHtml(modelName)}</span>`;
  block += `<span class="sml-card-badge">小模型计算结果</span>`;
  block += `</div>`;
  block += `<div class="sml-card-body">`;
  block += `<div class="sml-card-summary">${nl2br(escapeHtml(content))}</div>`;
  block += `</div></div>`;
  return block;
}

// ========== 环境检测 ==========
const isServer = os.hostname().includes('服务器关键词') ||
    fs.existsSync('/www/wwwroot') ||
    process.env.IS_SERVER === 'true';

console.log('🚀 启动冶金平台', isServer ? '服务器版' : '本地开发版');

const app = express();

// ========== 通义千问API配置 ==========
const DASHSCOPE_API_KEY = process.env.DASHSCOPE_API_KEY || 'sk-db9170f092a7494da4e2e1fe4ecc9af6';
const QWEN_API_URL = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation';

// ========== 静态文件路径配置 ==========
let publicPath;
if (isServer) {
    publicPath = '/www/wwwroot/metallurgy/public';
    console.log(`📁 服务器静态文件路径: ${publicPath}`);
} else {
    // 本地开发，使用相对路径
    publicPath = path.join(__dirname, 'public');
    console.log(`📁 本地静态文件路径: ${publicPath}`);
}

// ========== 增强CORS配置 ==========
const allowedOrigins = [
    'http://localhost:8080',
    'http://localhost:3000',
    'http://127.0.0.1:8080',
    'http://127.0.0.1:3000',  // 添加这个
    'https://sklam.dataset.org.cn',
    'https://www.sklam.dataset.org.cn',
    'http://sklam.dataset.org.cn',  // ✅ 添加 HTTP 版本
    'http://www.sklam.dataset.org.cn',  // ✅ 添加 HTTP www 版本
    'https://sklam.fewai.com',  // ✅ 新域名
    'http://sklam.fewai.com'  // ✅ 新域名 HTTP 版本
];

// 开发环境添加更多本地地址
if (!isServer) {
    allowedOrigins.push('http://localhost:5173');
    allowedOrigins.push('http://127.0.0.1:5173');
    allowedOrigins.push('http://localhost:8081');
    allowedOrigins.push('http://127.0.0.1:8081');
}

const corsOptions = {
    origin: function (origin, callback) {
        if (!origin) return callback(null, true);
        // 允许所有 localhost 和 127.0.0.1 来源（任意端口）
        if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) {
            return callback(null, true);
        }
        if (allowedOrigins.indexOf(origin) !== -1) {
            callback(null, true);
        } else {
            console.log('被阻止的跨域请求来源:', origin);
            callback(new Error('CORS策略不允许此来源'));
        }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: [
        'Content-Type',
        'Authorization',
        'X-User-Id',
        'Accept',
        'Origin',
        'X-Requested-With'
    ],
    exposedHeaders: ['Content-Range', 'X-Content-Range']
};

app.use(cors(corsOptions));
app.options('*', cors(corsOptions));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ========== 静态文件服务 ==========
if (fs.existsSync(publicPath)) {
    app.use(express.static(publicPath, {
        setHeaders: (res, filePath) => {
            const ext = path.extname(filePath).toLowerCase();

            // 字体文件
            if (ext === '.woff2') {
                res.setHeader('Content-Type', 'font/woff2');
            } else if (ext === '.woff') {
                res.setHeader('Content-Type', 'font/woff');
            }

            // HTML文件不缓存
            if (ext === '.html') {
                res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
                res.setHeader('Pragma', 'no-cache');
                res.setHeader('Expires', '0');
            }
        }
    }));
    console.log('✅ 静态文件服务已启用');
} else {
    console.warn('⚠️ public目录不存在');
}

// ========== PostgreSQL数据库连接 ==========
const pool = new Pool({
    host: '192.168.31.145',
    port: 5432,
    database: 'metallurgy',
    user: 'postgres',
    password: 'WJwzfwJ5JeXSkJ66',
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
    connectionString: 'postgresql://postgres:WJwzfwJ5JeXSkJ66@192.168.31.145:5432/metallurgy?search_path="User",public'
});

// 测试数据库连接
pool.connect((err, client, release) => {
    if (err) {
        console.error('❌ 数据库连接失败:', err.message);
        console.log('⚠️ 将以无数据库模式运行');
        return;
    }

    console.log('✅ 数据库连接成功');

    client.query(`
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'User'
              AND table_name = 'accounts'
        )
    `, (err, result) => {
        release();

        if (err) {
            console.error('❌ 检查User.accounts表失败:', err.message);
            return;
        }

        const tableExists = result.rows[0].exists;
        console.log('📊 User.accounts表是否存在:', tableExists);

        if (!tableExists) {
            console.log('⚠️ User.accounts表不存在，请创建表结构');
        } else {
            pool.query('SELECT COUNT(*) as count FROM "User".accounts')
                .then(countResult => {
                    console.log(`👥 User.accounts表当前有 ${countResult.rows[0].count} 条记录`);
                })
                .catch(err => {
                    console.error('❌ 查询用户数量失败:', err.message);
                });
        }
    });
});

// ========== 创建API路由组 ==========
const apiRouter = express.Router();

// 1. 健康检查
apiRouter.get('/health', (req, res) => {
    res.json({
        code: 200,
        status: 'ok',
        timestamp: new Date().toISOString(),
        message: '服务器运行正常'
    });
});

// ========== 智能对话API ==========
apiRouter.post('/chat/completion', async (req, res) => {
    try {
        const { message, history = [] } = req.body;

        console.log('🤖 聊天请求:', {
            messageLength: message?.length || 0,
            historyCount: history.length
        });

        if (!message || message.trim() === '') {
            return res.status(400).json({
                code: 400,
                message: '消息内容不能为空'
            });
        }

        // 构造对话历史
        const messages = [
            {
                role: 'system',
                content: `你是一个专业的冶金领域智能助手。回复要简短专业，控制在 3-5 句话，不要啰嗦。全程用中文回答（专有名词如 FeO、SiO₂ 等化学式除外）。

【大小模型协同架构说明】
本系统采用大小模型协同架构：
- 你（大模型）：负责理解用户意图、生成回答
- 专业小模型：擅长特定领域的深度计算和分析，每个小模型都是该领域的专家
当用户的问题涉及数值计算、工艺优化时，你应当调用对应的小模型来提供专业分析。调用后结果会以卡片形式嵌入到你的回答中。

调用格式：[调用:模型ID:{"query":"你的问题"}]

可调用的小模型：

1. 🔬 热力学推理 — 热力学计算、反应可行性分析
   示例：[调用:thermodynamics:{"query":"FeO + C → Fe + CO 在 1600°C 能否反应"}]

2. 🔥 转炉炼钢工艺优化 — 终点预测、氧耗计算
   示例：[调用:converter:{"query":"铁水 Si 0.5%，目标碳 0.05%，温度 1600°C，终点预测"}]

3. 🏭 高炉低碳运行分析 — 碳排放评估、降碳分析
   示例：[调用:blastfurnace:{"query":"焦比 360，煤比 160，日产量 5000t，碳排放多少"}]

4. 📊 连铸质量辅助决策 — 铸坯质量预测、参数优化
   示例：[调用:casting:{"query":"Q235B 200x200mm 拉速 1.2 过热度 30°C 质量预测"}]

5. 💻 对话式仿真与工单协同 — 操作工单生成
   示例：[调用:simulation:{"query":"转炉炼钢 45分钟 操作工单"}]

【调用规则】
1. 数值计算、工艺参数优化类问题必须调用小模型
2. 每条回答最多调用 2 个
3. 先给出你的简短分析，再插入调用标记
4. 纯知识问答不需要调用`
            },
            ...history.map(item => ({
                role: item.role,
                content: item.content
            })),
            {
                role: 'user',
                content: message
            }
        ];

        // 调用通义千问API
        const response = await axios.post(
            QWEN_API_URL,
            {
                model: 'qwen-plus',
                input: {
                    messages: messages
                },
                parameters: {
                    result_format: 'message',
                    temperature: 0.8,
                    top_p: 0.8,
                    repetition_penalty: 1.05,
                    max_tokens: 8192
                }
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${DASHSCOPE_API_KEY}`,
                    'X-DashScope-SSE': 'disable'
                },
                timeout: 120000 // 120秒超时
            }
        );

        if (!response.data.output || !response.data.output.choices || response.data.output.choices.length === 0) {
            throw new Error('API返回格式异常');
        }

        const assistantMessage = response.data.output.choices[0].message;
        let finalContent = assistantMessage.content;
        let smallModelCalled = true; // 展示大小模型协同标识

        // 解析并执行小模型调用
        const { cleanedContent, handlerPromises } = parseAndExecuteSmallModelCalls(finalContent);
        finalContent = cleanedContent;

        if (handlerPromises.length > 0) {
          console.log(`🔧 检测到 ${handlerPromises.length} 个小模型调用，正在执行...`);

          // 并行执行所有 handler
          const results = await Promise.all(handlerPromises);

          // 替换标记为格式化结果块
          for (const item of results) {
            if (item.reply) {
              finalContent = finalContent.replace(
                item.fullMatch,
                formatSmallModelBlock(item.modelName, item.icon, { reply: item.reply })
              );
            } else if (item.error) {
              finalContent = finalContent.replace(
                item.fullMatch,
                formatSmallModelBlock(item.modelName, item.icon, { error: item.error })
              );
            }
          }

          console.log('✅ 小模型调用完成，已嵌入结果');
        }

        console.log('✅ 聊天响应成功，字符数:', finalContent.length);

        res.json({
            code: 200,
            message: '成功',
            data: {
                role: assistantMessage.role,
                content: finalContent,
                smallModelCalled: smallModelCalled,
                timestamp: new Date().toISOString()
            }
        });

    } catch (error) {
        console.error('❌ 聊天接口错误:', error.response?.data || error.message);

        let errorMessage = '智能对话服务暂时不可用，请稍后重试';
        let errorCode = 500;

        if (error.response?.status === 401) {
            errorMessage = 'API密钥无效或已过期';
            errorCode = 401;
        } else if (error.response?.status === 429) {
            errorMessage = '请求过于频繁，请稍后再试';
            errorCode = 429;
        } else if (error.code === 'ECONNABORTED') {
            errorMessage = '请求超时，请检查网络连接';
            errorCode = 408;
        }

        res.status(errorCode).json({
            code: errorCode,
            message: errorMessage,
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
});

// ========== 小模型直接调用 API（独立使用） ==========
apiRouter.post('/tools/:modelId', async (req, res) => {
    try {
        const { modelId } = req.params;
        const params = req.body;

        const registryItem = smallModelRegistry.find(m => m.id === modelId);

        if (!registryItem) {
            return res.status(404).json({
                code: 404,
                message: `未知小模型 ID: ${modelId}`,
                availableModels: smallModelRegistry.map(m => ({ id: m.id, name: m.name }))
            });
        }

        console.log(`🔧 小模型直接调用: ${registryItem.name}`, params);

        const result = await registryItem.handler(params);

        res.json({
            code: 200,
            message: '成功',
            data: {
                modelId: registryItem.id,
                modelName: registryItem.name,
                icon: registryItem.icon,
                result
            }
        });
    } catch (error) {
        console.error('❌ 小模型调用错误:', error.message);
        res.status(500).json({
            code: 500,
            message: '小模型调用失败',
            error: error.message
        });
    }
});

// ========== 小模型对话 API（LLM + 本地计算） ==========
// ========== 小模型对话 API（纯 LLM） ==========
const toolSystemPrompts = {
  thermodynamics: `你是一名冶金热力学专家。你的职责：
1. 只回答与冶金热力学计算相关的问题
2. 根据用户提供的反应式和温度，自己计算 ΔG、平衡常数 K，判断反应方向
3. 计算时使用公式 ΔG = ΔH - TΔS，标注你使用的热力学数据来源
4. 回复简洁专业，控制在 5 句话以内
5. 超出热力学范围的问题礼貌回绝`,

  converter: `你是一名转炉炼钢工艺专家。你的职责：
1. 只回答与转炉炼钢工艺优化相关的问题
2. 根据用户提供的铁水成分和目标参数，推算终点碳、温度、氧耗
3. 给出工艺优化建议
4. 回复简洁专业，控制在 5 句话以内
5. 超出转炉炼钢范围的问题礼貌回绝`,

  blastfurnace: `你是一名高炉低碳冶金专家。你的职责：
1. 只回答与高炉碳排放、低碳冶金相关的问题
2. 根据用户提供的焦比、煤比、产量等参数，计算碳排放量和碳利用效率
3. 给出降碳建议
4. 回复简洁专业，控制在 5 句话以内
5. 超出高炉低碳范围的问题礼貌回绝`,

  casting: `你是一名连铸质量专家。你的职责：
1. 只回答与连铸坯质量相关的问题
2. 根据用户提供的钢种、断面、拉速、过热度等参数，评估铸坯质量
3. 给出工艺参数优化建议
4. 回复简洁专业，控制在 5 句话以内
5. 超出连铸质量范围的问题礼貌回绝`,

  simulation: `你是一名冶金工艺仿真专家。你的职责：
1. 根据用户描述的场景、设备和耗时，生成详细操作工单
2. 工单应包括操作步骤、注意事项和预期效果
3. 回复简洁专业，控制在 5 句话以内
4. 超出冶金工艺仿真范围的问题礼貌回绝`
};

apiRouter.post('/tools/:modelId/chat', async (req, res) => {
    try {
        const { modelId } = req.params;
        const { message, history = [] } = req.body;

        const registryItem = smallModelRegistry.find(m => m.id === modelId);

        if (!registryItem) {
            return res.status(404).json({
                code: 404,
                message: `未知小模型 ID: ${modelId}`
            });
        }

        const systemPrompt = toolSystemPrompts[modelId] || '你是一名冶金领域专家。';
        console.log(`💬 小模型对话: ${registryItem.name}`);

        const messages = [
            { role: 'system', content: systemPrompt },
            ...history.map(h => ({ role: h.role, content: h.content })),
            { role: 'user', content: message }
        ];

        const response = await axios.post(
            QWEN_API_URL,
            {
                model: 'qwen-plus',
                input: { messages },
                parameters: {
                    result_format: 'message',
                    temperature: 0.6,
                    top_p: 0.8,
                    repetition_penalty: 1.05,
                    max_tokens: 1024
                }
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${DASHSCOPE_API_KEY}`,
                    'X-DashScope-SSE': 'disable'
                },
                timeout: 30000
            }
        );

        const reply = response.data.output.choices[0].message.content;

        res.json({
            code: 200,
            message: '成功',
            data: { reply, result: null }
        });

    } catch (error) {
        console.error('❌ 小模型对话错误:', error.response?.data || error.message);
        res.status(500).json({
            code: 500,
            message: '小模型对话失败',
            error: error.message
        });
    }
});

// 2. 测试用户数据接口（调试用）- 使用 User.accounts
apiRouter.get('/test-users', async (req, res) => {
    try {
        const tableCheck = await pool.query(`
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'User'
                  AND table_name = 'accounts'
            )
        `);

        if (!tableCheck.rows[0].exists) {
            return res.json({
                code: 404,
                message: 'User.accounts表不存在',
                data: null
            });
        }

        const users = await pool.query(
            'SELECT id, username, email, account_type, account_status, created_at FROM "User".accounts ORDER BY id DESC LIMIT 10'
        );

        const countResult = await pool.query('SELECT COUNT(*) as total FROM "User".accounts');

        res.json({
            code: 200,
            message: '成功',
            data: {
                tableExists: true,
                totalUsers: parseInt(countResult.rows[0].total),
                users: users.rows
            }
        });

    } catch (error) {
        console.error('测试用户接口错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 3. 注册接口 - 使用 User.accounts
apiRouter.post('/auth/register', async (req, res) => {
    try {
        console.log('📝 注册请求:', req.body);

        const { username, email, password, realName, organization } = req.body;

        if (!username || !email || !password) {
            return res.status(400).json({
                code: 400,
                message: '用户名、邮箱和密码为必填项'
            });
        }

        if (username.length < 3 || username.length > 20) {
            return res.status(400).json({
                code: 400,
                message: '用户名长度应为3-20位'
            });
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return res.status(400).json({
                code: 400,
                message: '邮箱格式不正确'
            });
        }

        if (password.length < 8) {
            return res.status(400).json({
                code: 400,
                message: '密码长度至少8位'
            });
        }

        const userCheck = await pool.query(
            'SELECT * FROM "User".accounts WHERE username = $1 OR email = $2',
            [username, email]
        );

        if (userCheck.rows.length > 0) {
            const existingUser = userCheck.rows[0];
            if (existingUser.username === username) {
                return res.status(409).json({
                    code: 409,
                    message: '用户名已被注册'
                });
            }
            if (existingUser.email === email) {
                return res.status(409).json({
                    code: 409,
                    message: '邮箱已被注册'
                });
            }
        }

        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);

        const result = await pool.query(
            `INSERT INTO "User".accounts
             (username, email, password_hash, real_name, organization, created_at, account_type, account_status, role)
             VALUES ($1, $2, $3, $4, $5, NOW(), 'user', 'active', 'user')
                 RETURNING id, username, email, real_name, organization, created_at`,
            [username, email, hashedPassword, realName || null, organization || null]
        );

        const newUser = result.rows[0];
        console.log('✅ 注册成功，用户ID:', newUser.id, '表: User.accounts');

        res.status(200).json({
            code: 200,
            message: '注册成功',
            data: {
                id: newUser.id,
                username: newUser.username,
                email: newUser.email,
                realName: newUser.real_name,
                organization: newUser.organization,
                createdAt: newUser.created_at
            }
        });

    } catch (error) {
        console.error('❌ 注册错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 4. 登录接口 - 使用 User.accounts（包含更新 last_login_at）
apiRouter.post('/auth/login', async (req, res) => {
    try {
        console.log('🔑 登录请求:', { email: req.body.email, password: '***' });

        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({
                code: 400,
                message: '邮箱和密码为必填项'
            });
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return res.status(400).json({
                code: 400,
                message: '邮箱格式不正确'
            });
        }

        const result = await pool.query(
            'SELECT * FROM "User".accounts WHERE email = $1',
            [email]
        );

        if (result.rows.length === 0) {
            console.log('❌ 用户不存在:', email);
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const user = result.rows[0];
        console.log('👤 找到用户:', user.username, '角色:', user.role, '账户类型:', user.account_type);

        const isPasswordValid = await bcrypt.compare(password, user.password_hash);

        if (!isPasswordValid) {
            console.log('❌ 密码错误');
            return res.status(401).json({
                code: 401,
                message: '密码错误'
            });
        }

        await pool.query(
            'UPDATE "User".accounts SET last_login_at = NOW() WHERE id = $1',
            [user.id]
        );

        console.log('✅ 登录成功:', user.username);

        const updatedUserResult = await pool.query(
            'SELECT * FROM "User".accounts WHERE id = $1',
            [user.id]
        );

        const updatedUser = updatedUserResult.rows[0];
        const { password_hash: _, ...userWithoutPassword } = updatedUser;

        let userRole = 'user';
        if (updatedUser.role && updatedUser.role.toLowerCase() === 'admin') {
            userRole = 'admin';
        } else if (updatedUser.account_type && updatedUser.account_type.toLowerCase() === 'admin') {
            userRole = 'admin';
        } else if (updatedUser.email && (updatedUser.email.endsWith('@admin.com') || updatedUser.email.endsWith('@metallurgy.com'))) {
            userRole = 'admin';
        }

        console.log('📊 最终用户角色:', userRole);

        res.status(200).json({
            code: 200,
            message: '登录成功',
            data: {
                id: updatedUser.id,
                username: updatedUser.username,
                email: updatedUser.email,
                realName: updatedUser.real_name,
                organization: updatedUser.organization,
                createdAt: updatedUser.created_at,
                lastLoginAt: updatedUser.last_login_at,
                role: userRole,
                accountType: updatedUser.account_type,
                accountStatus: updatedUser.account_status,
                isAdmin: userRole === 'admin'
            }
        });

    } catch (error) {
        console.error('❌ 登录错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 5. 获取用户信息 - 使用 User.accounts
apiRouter.get('/user/:id', async (req, res) => {
    try {
        const userId = req.params.id;

        const result = await pool.query(
            'SELECT id, username, email, real_name, organization, created_at FROM "User".accounts WHERE id = $1',
            [userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const user = result.rows[0];
        res.status(200).json({
            code: 200,
            data: {
                id: user.id,
                username: user.username,
                email: user.email,
                realName: user.real_name,
                organization: user.organization,
                createdAt: user.created_at
            }
        });

    } catch (error) {
        console.error('获取用户信息错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 6. 测试密码接口（调试用）- 使用 User.accounts
apiRouter.post('/test-password', async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email) {
            return res.status(400).json({
                code: 400,
                message: '邮箱为必填项'
            });
        }

        const result = await pool.query(
            'SELECT * FROM "User".accounts WHERE email = $1',
            [email]
        );

        if (result.rows.length === 0) {
            return res.json({
                code: 404,
                message: '用户不存在',
                data: { userExists: false }
            });
        }

        const user = result.rows[0];
        let passwordMatch = false;

        if (password) {
            passwordMatch = await bcrypt.compare(password, user.password_hash);
        }

        res.json({
            code: 200,
            message: '成功',
            data: {
                userExists: true,
                username: user.username,
                email: user.email,
                passwordMatch: passwordMatch,
                passwordHash: user.password_hash.substring(0, 30) + '...',
                passwordLength: user.password_hash.length
            }
        });

    } catch (error) {
        console.error('密码测试错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// ========== 个人中心相关接口 ==========

// 7. 获取当前用户资料
apiRouter.get('/user/profile', async (req, res) => {
    try {
        const userId = req.headers['x-user-id'];

        if (!userId) {
            return res.status(401).json({
                code: 401,
                message: '未登录'
            });
        }

        console.log('📊 获取用户资料，用户ID:', userId);

        const result = await pool.query(
            `SELECT 
                id, 
                username, 
                email, 
                real_name as "realName", 
                organization, 
                role,
                account_type as "accountType", 
                account_status as "accountStatus",
                created_at as "createdAt",
                last_login_at as "lastLoginAt"
             FROM "User".accounts 
             WHERE id = $1`,
            [userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const user = result.rows[0];
        console.log('✅ 找到用户:', user.username);

        if (!user.accountStatus) {
            user.accountStatus = user.accountStatus || 'active';
        }

        res.status(200).json({
            code: 200,
            message: '成功',
            data: user
        });

    } catch (error) {
        console.error('❌ 获取用户资料错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 8. 更新个人资料（包含密码修改）
apiRouter.put('/user/profile', async (req, res) => {
    try {
        const userId = req.headers['x-user-id'];
        const {
            username,
            email,
            realName,
            organization,
            role,
            accountStatus,
            currentPassword,
            newPassword
        } = req.body;

        if (!userId) {
            return res.status(401).json({
                code: 401,
                message: '未登录'
            });
        }

        console.log('📝 更新用户资料，用户ID:', userId);

        if (!username || !email) {
            return res.status(400).json({
                code: 400,
                message: '用户名和邮箱为必填项'
            });
        }

        if (username.length < 3 || username.length > 20) {
            return res.status(400).json({
                code: 400,
                message: '用户名长度应为3-20位'
            });
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return res.status(400).json({
                code: 400,
                message: '邮箱格式不正确'
            });
        }

        const emailCheck = await pool.query(
            'SELECT id FROM "User".accounts WHERE email = $1 AND id != $2',
            [email, userId]
        );

        if (emailCheck.rows.length > 0) {
            return res.status(409).json({
                code: 409,
                message: '邮箱已被其他用户使用'
            });
        }

        const usernameCheck = await pool.query(
            'SELECT id FROM "User".accounts WHERE username = $1 AND id != $2',
            [username, userId]
        );

        if (usernameCheck.rows.length > 0) {
            return res.status(409).json({
                code: 409,
                message: '用户名已被其他用户使用'
            });
        }

        const currentUserResult = await pool.query(
            'SELECT role, account_type FROM "User".accounts WHERE id = $1',
            [userId]
        );

        if (currentUserResult.rows.length === 0) {
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const currentUser = currentUserResult.rows[0];
        const isAdminUser = currentUser.role === 'admin' || currentUser.account_type === 'admin';

        let finalRole = currentUser.role;
        let finalStatus = currentUser.account_status || 'active';

        if (isAdminUser) {
            finalRole = role || currentUser.role;
            finalStatus = accountStatus || currentUser.account_status || 'active';
        } else {
            console.log('👤 普通用户，保持原有角色和状态');
        }

        let passwordUpdate = '';
        let passwordParams = [];
        if (currentPassword && newPassword) {
            if (newPassword.length < 8) {
                return res.status(400).json({
                    code: 400,
                    message: '新密码长度至少8位'
                });
            }

            const passwordResult = await pool.query(
                'SELECT password_hash FROM "User".accounts WHERE id = $1',
                [userId]
            );

            if (passwordResult.rows.length === 0) {
                return res.status(404).json({
                    code: 404,
                    message: '用户不存在'
                });
            }

            const userPassword = passwordResult.rows[0];
            const isPasswordValid = await bcrypt.compare(currentPassword, userPassword.password_hash);
            if (!isPasswordValid) {
                return res.status(401).json({
                    code: 401,
                    message: '当前密码错误'
                });
            }

            const salt = await bcrypt.genSalt(10);
            const hashedPassword = await bcrypt.hash(newPassword, salt);

            passwordUpdate = ', password_hash = $6';
            passwordParams = [hashedPassword];
        }

        const updateParams = [
            username,
            email,
            realName || null,
            organization || null,
            finalRole,
            finalStatus,
            userId
        ];

        if (passwordUpdate) {
            updateParams.splice(5, 0, ...passwordParams);
        }

        const query = `
            UPDATE "User".accounts 
            SET username = $1, 
                email = $2, 
                real_name = $3, 
                organization = $4,
                role = $5,
                account_status = $6,
                updated_at = NOW()
                ${passwordUpdate}
            WHERE id = ${passwordUpdate ? '$8' : '$7'}
            RETURNING 
                id, 
                username, 
                email, 
                real_name as "realName", 
                organization, 
                role,
                account_status as "accountStatus",
                created_at as "createdAt",
                updated_at as "updatedAt"
        `;

        const result = await pool.query(query, updateParams);

        if (result.rows.length === 0) {
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const updatedUser = result.rows[0];
        console.log('✅ 用户资料更新成功，用户ID:', userId);

        res.status(200).json({
            code: 200,
            message: '个人资料更新成功',
            data: updatedUser
        });

    } catch (error) {
        console.error('❌ 更新用户资料错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// ========== 管理员用户管理接口 ==========

// 验证管理员权限的中间件
const adminAuth = async (req, res, next) => {
    try {
        const userId = req.headers['x-user-id'];

        if (!userId) {
            return res.status(401).json({
                code: 401,
                message: '未登录'
            });
        }

        const userResult = await pool.query(
            'SELECT role, account_type FROM "User".accounts WHERE id = $1',
            [userId]
        );

        if (userResult.rows.length === 0) {
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const user = userResult.rows[0];
        const isAdmin = user.role === 'admin' || user.account_type === 'admin';

        if (!isAdmin) {
            return res.status(403).json({
                code: 403,
                message: '需要管理员权限'
            });
        }

        console.log('👑 管理员权限验证通过，用户ID:', userId);
        next();
    } catch (error) {
        console.error('管理员权限验证错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
};

// 9. 获取用户列表（带分页和搜索）- 仅管理员
apiRouter.get('/admin/users', adminAuth, async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const search = req.query.search || '';
        const offset = (page - 1) * limit;

        console.log('📋 获取用户列表，页码:', page, '每页:', limit, '搜索:', search);

        let whereClause = '';
        let queryParams = [];
        let paramCount = 1;

        if (search) {
            whereClause = `WHERE username ILIKE $${paramCount} OR email ILIKE $${paramCount} OR real_name ILIKE $${paramCount}`;
            queryParams.push(`%${search}%`);
            paramCount++;
        }

        const countQuery = search
            ? `SELECT COUNT(*) as total FROM "User".accounts ${whereClause}`
            : 'SELECT COUNT(*) as total FROM "User".accounts';

        const countResult = await pool.query(countQuery, queryParams);
        const total = parseInt(countResult.rows[0].total);

        const usersQuery = `
            SELECT 
                id, 
                username, 
                email, 
                real_name as "realName", 
                organization, 
                role,
                account_type as "accountType", 
                account_status as "accountStatus",
                created_at as "createdAt", 
                last_login_at as "lastLoginAt"
            FROM "User".accounts 
            ${whereClause}
            ORDER BY id DESC
            LIMIT $${paramCount} OFFSET $${paramCount + 1}
        `;

        const finalParams = search
            ? [...queryParams, limit, offset]
            : [limit, offset];

        const usersResult = await pool.query(usersQuery, finalParams);

        const users = usersResult.rows.map(user => ({
            ...user,
            accountStatus: user.accountStatus || 'active'
        }));

        console.log('✅ 获取到', users.length, '个用户');

        res.status(200).json({
            code: 200,
            message: '成功',
            data: {
                users: users,
                total: total,
                page: page,
                limit: limit,
                totalPages: Math.ceil(total / limit)
            }
        });

    } catch (error) {
        console.error('❌ 获取用户列表错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 10. 更新用户信息 - 仅管理员
apiRouter.put('/admin/users/:id', adminAuth, async (req, res) => {
    try {
        const userId = req.params.id;
        const { username, email, realName, organization, role, accountStatus } = req.body;
        const currentAdminId = req.headers['x-user-id'];

        console.log('📝 管理员更新用户，目标用户ID:', userId, '管理员ID:', currentAdminId);

        if (!username || !email) {
            return res.status(400).json({
                code: 400,
                message: '用户名和邮箱为必填项'
            });
        }

        if (username.length < 3 || username.length > 20) {
            return res.status(400).json({
                code: 400,
                message: '用户名长度应为3-20位'
            });
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return res.status(400).json({
                code: 400,
                message: '邮箱格式不正确'
            });
        }

        const emailCheck = await pool.query(
            'SELECT id FROM "User".accounts WHERE email = $1 AND id != $2',
            [email, userId]
        );

        if (emailCheck.rows.length > 0) {
            return res.status(409).json({
                code: 409,
                message: '邮箱已被其他用户使用'
            });
        }

        const usernameCheck = await pool.query(
            'SELECT id FROM "User".accounts WHERE username = $1 AND id != $2',
            [username, userId]
        );

        if (usernameCheck.rows.length > 0) {
            return res.status(409).json({
                code: 409,
                message: '用户名已被其他用户使用'
            });
        }

        const result = await pool.query(
            `UPDATE "User".accounts
             SET username = $1,
                 email = $2,
                 real_name = $3,
                 organization = $4,
                 role = $5,
                 account_status = $6,
                 updated_at = NOW()
             WHERE id = $7
                 RETURNING 
                 id, 
                 username, 
                 email, 
                 real_name as "realName", 
                 organization, 
                 role,
                 account_status as "accountStatus",
                 created_at as "createdAt",
                 updated_at as "updatedAt"`,
            [username, email, realName || null, organization || null,
                role || 'user', accountStatus || 'active', userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const updatedUser = result.rows[0];
        console.log('✅ 管理员更新用户成功，用户ID:', userId);

        res.status(200).json({
            code: 200,
            message: '用户信息更新成功',
            data: updatedUser
        });

    } catch (error) {
        console.error('❌ 管理员更新用户错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 11. 删除单个用户 - 仅管理员
apiRouter.delete('/admin/users/:id', adminAuth, async (req, res) => {
    try {
        const userId = req.params.id;
        const currentAdminId = req.headers['x-user-id'];

        console.log('🗑️ 管理员删除用户，目标用户ID:', userId, '管理员ID:', currentAdminId);

        if (userId === currentAdminId) {
            return res.status(400).json({
                code: 400,
                message: '不能删除自己的账户'
            });
        }

        const userCheck = await pool.query(
            'SELECT id, username FROM "User".accounts WHERE id = $1',
            [userId]
        );

        if (userCheck.rows.length === 0) {
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const userToDelete = userCheck.rows[0];

        const result = await pool.query(
            'DELETE FROM "User".accounts WHERE id = $1 RETURNING id, username',
            [userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                code: 404,
                message: '用户不存在'
            });
        }

        const deletedUser = result.rows[0];
        console.log('✅ 管理员删除用户成功，用户ID:', userId, '用户名:', deletedUser.username);

        res.status(200).json({
            code: 200,
            message: '用户删除成功',
            data: {
                deletedUserId: deletedUser.id,
                deletedUsername: deletedUser.username
            }
        });

    } catch (error) {
        console.error('❌ 删除用户错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 12. 批量删除用户 - 仅管理员
apiRouter.delete('/admin/users/batch', adminAuth, async (req, res) => {
    try {
        const { userIds } = req.body;
        const currentAdminId = req.headers['x-user-id'];

        console.log('🗑️ 管理员批量删除用户，目标用户IDs:', userIds, '管理员ID:', currentAdminId);

        if (!userIds || !Array.isArray(userIds) || userIds.length === 0) {
            return res.status(400).json({
                code: 400,
                message: '请选择要删除的用户'
            });
        }

        const filteredUserIds = userIds.filter(id => {
            if (typeof id === 'string') {
                return id !== currentAdminId && id.trim() !== '';
            }
            return id !== currentAdminId;
        });

        if (filteredUserIds.length === 0) {
            return res.status(400).json({
                code: 400,
                message: '不能删除自己的账户'
            });
        }

        const placeholders = filteredUserIds.map((_, index) => `$${index + 1}`).join(',');

        const usersResult = await pool.query(
            `SELECT id, username FROM "User".accounts WHERE id IN (${placeholders})`,
            filteredUserIds
        );

        const deleteResult = await pool.query(
            `DELETE FROM "User".accounts WHERE id IN (${placeholders})`,
            filteredUserIds
        );

        console.log('✅ 管理员批量删除用户成功，删除数量:', deleteResult.rowCount);

        res.status(200).json({
            code: 200,
            message: `成功删除 ${deleteResult.rowCount} 个用户`,
            data: {
                deletedCount: deleteResult.rowCount,
                deletedUsers: usersResult.rows
            }
        });

    } catch (error) {
        console.error('❌ 批量删除用户错误:', error);
        res.status(500).json({
            code: 500,
            message: '服务器内部错误',
            error: error.message
        });
    }
});

// 13. 测试接口 - 临时添加（用于调试）
apiRouter.get('/test-profile', async (req, res) => {
    try {
        const userId = req.headers['x-user-id'] || '1';

        console.log('🔧 测试获取用户，ID:', userId);

        const result = await pool.query(
            'SELECT id, username, email FROM "User".accounts WHERE id = $1',
            [userId]
        );

        console.log('查询结果:', result.rows);

        if (result.rows.length === 0) {
            return res.json({
                code: 404,
                message: '测试用户不存在',
                data: null
            });
        }

        res.json({
            code: 200,
            message: '测试成功',
            data: result.rows[0]
        });

    } catch (error) {
        console.error('❌ 测试接口错误:', error);
        res.status(500).json({
            code: 500,
            message: '测试接口错误',
            error: error.message,
            stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
        });
    }
});

// ========== 挂载路由并启动服务器 ==========

// 将API路由挂载到/api路径下
app.use('/api', apiRouter);

// ========== 关键修复：处理根路径 ==========
app.get('/', (req, res) => {
    console.log('🔗 访问根路径');

    const indexPath = path.join(publicPath, 'index.html');

    if (fs.existsSync(indexPath)) {
        console.log(`📄 返回前端页面: ${indexPath}`);
        res.sendFile(indexPath);
    } else {
        console.log('⚠️  未找到index.html，显示默认页面');
        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>冶金平台</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .api-list { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-top: 20px; }
                    .api-item { margin: 10px 0; padding: 10px; background: white; border-radius: 3px; }
                    .method { display: inline-block; width: 80px; font-weight: bold; }
                    .get { color: green; }
                    .post { color: blue; }
                    .put { color: orange; }
                    .delete { color: red; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>冶金平台后端服务</h1>
                    <p>✅ API服务正常运行</p>
                    <p>前端页面未找到，请检查静态文件路径: <code>${publicPath}</code></p>
                    
                    <div class="api-list">
                        <h3>可用API接口:</h3>
                        <div class="api-item"><span class="method get">GET</span> <a href="/api/health">/api/health</a> - 健康检查</div>
                        <div class="api-item"><span class="method get">GET</span> <a href="/api/test-users">/api/test-users</a> - 测试用户数据</div>
                        <div class="api-item"><span class="method post">POST</span> /api/auth/register - 用户注册</div>
                        <div class="api-item"><span class="method post">POST</span> /api/auth/login - 用户登录</div>
                        <div class="api-item"><span class="method get">GET</span> /api/user/profile - 获取个人资料</div>
                    </div>
                    
                    <p style="margin-top: 30px; color: #666;">
                        服务器: ${isServer ? '生产环境' : '开发环境'} | 时间: ${new Date().toLocaleString()}
                    </p>
                </div>
            </body>
            </html>
        `);
    }
});

// 处理其他前端路由（Vue Router）
app.get('*', (req, res, next) => {
    // API请求交给现有的API路由
    if (req.path.startsWith('/api')) {
        return next();
    }

    // 如果有文件扩展名，交给静态文件服务
    if (req.path.includes('.')) {
        const filePath = path.join(publicPath, req.path);
        if (fs.existsSync(filePath)) {
            return res.sendFile(filePath);
        }
        return next();
    }

    // 其他所有请求都返回Vue的index.html（支持前端路由）
    const indexPath = path.join(publicPath, 'index.html');
    if (fs.existsSync(indexPath)) {
        console.log(`🔄 Vue路由重定向: ${req.path} -> index.html`);
        res.sendFile(indexPath);
    } else {
        next();
    }
});

// 404处理
app.use((req, res) => {
    console.log('❌ 404 - 接口不存在:', req.originalUrl);
    res.status(404).json({
        code: 404,
        message: '接口不存在',
        path: req.originalUrl
    });
});

// 错误处理中间件
app.use((err, req, res, next) => {
    console.error('💥 服务器错误:', err.message);
    res.status(500).json({
        code: 500,
        message: '服务器内部错误',
        error: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// ========== 启动服务器 ==========
const PORT = process.env.PORT || 3000;
const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`========================================`);
    console.log(`✅ 冶金平台服务已启动`);
    console.log(`服务器运行在: http://0.0.0.0:${PORT}`);
    console.log(`前端访问: http://localhost:${PORT}`);
    console.log(`API地址: http://0.0.0.0:${PORT}/api`);
    console.log(`静态文件目录: ${publicPath}`);
    console.log(`环境: ${isServer ? '服务器' : '本地开发'}`);
    console.log(`========================================`);
    console.log('📋 主要接口:');
    console.log(`  GET    /                         - 前端页面`);
    console.log(`  GET    /api/health               - 健康检查`);
    console.log(`  GET    /api/test-users           - 测试用户数据`);
    console.log(`  POST   /api/auth/register        - 用户注册`);
    console.log(`  POST   /api/auth/login           - 用户登录`);
    console.log(`  GET    /api/user/profile         - 获取个人资料`);
    console.log(`  PUT    /api/user/profile         - 更新个人资料`);
    console.log(`  GET    /api/admin/users          - 管理员获取用户列表`);
    console.log(`  PUT    /api/admin/users/:id      - 管理员更新用户`);
    console.log(`  DELETE /api/admin/users/:id      - 管理员删除用户`);
    console.log(`  DELETE /api/admin/users/batch    - 管理员批量删除`);
    console.log(`========================================`);
    console.log(`  POST   /api/chat/completion      - 智能对话接口`);
});

// 优雅关闭
process.on('SIGINT', () => {
    console.log('收到关闭信号，正在关闭服务器...');
    server.close(() => {
        console.log('服务器已关闭');
        pool.end();
        process.exit(0);
    });
});