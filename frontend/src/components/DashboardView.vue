<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import ChartCard from "./ChartCard.vue";

const emit = defineEmits(["open-list"]);
const dashboard = ref(null);
const loading = ref(true);
const error = ref("");

const statusLabels = { NEW: "待受理", ASSIGNED: "已分配", IN_PROGRESS: "处理中", RESOLVED: "已解决", CLOSED: "已关闭" };
const palette = ["#0f5ba7", "#00a6a6", "#f59e0b", "#ef6c5b", "#64748b", "#7c3aed"];

function pieOption(items, labels = {}) {
  return {
    color: palette,
    tooltip: { trigger: "item" },
    legend: { bottom: 0, textStyle: { color: "#52606d" } },
    series: [{
      type: "pie",
      radius: ["42%", "68%"],
      center: ["50%", "44%"],
      label: { formatter: "{b}\n{c}" },
      data: items.map((item) => ({ name: labels[item.name] || item.name, value: item.value })),
    }],
  };
}

const categoryOption = computed(() => ({
  color: ["#0f5ba7"],
  tooltip: { trigger: "axis" },
  grid: { left: 76, right: 20, top: 20, bottom: 30 },
  xAxis: { type: "value", splitLine: { lineStyle: { color: "#edf2f7" } } },
  yAxis: { type: "category", data: (dashboard.value?.by_category || []).map((x) => x.name).reverse(), axisLabel: { color: "#52606d" } },
  series: [{ type: "bar", data: (dashboard.value?.by_category || []).map((x) => x.value).reverse(), barWidth: 16, itemStyle: { borderRadius: [0, 5, 5, 0] } }],
}));

const trendOption = computed(() => {
  const rows = dashboard.value?.trend || [];
  return {
    color: ["#0f5ba7", "#00a6a6"],
    tooltip: { trigger: "axis" },
    legend: { data: ["新建", "已解决"], top: 0 },
    grid: { left: 42, right: 20, top: 38, bottom: 40 },
    xAxis: { type: "category", data: rows.map((x) => x.day.slice(5)), axisLabel: { color: "#64748b", rotate: 40 } },
    yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: "#edf2f7" } } },
    series: [
      { name: "新建", type: "line", smooth: true, data: rows.map((x) => x.created), areaStyle: { opacity: 0.08 } },
      { name: "已解决", type: "line", smooth: true, data: rows.map((x) => x.resolved) },
    ],
  };
});

async function loadDashboard() {
  loading.value = true;
  error.value = "";
  try {
    dashboard.value = await api.getDashboard();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

onMounted(loadDashboard);
defineExpose({ reload: loadDashboard });
</script>

<template>
  <div v-if="loading" class="state-card">正在加载运营数据…</div>
  <div v-else-if="error" class="state-card error">{{ error }}</div>
  <div v-else-if="dashboard" class="dashboard">
    <div class="section-heading">
      <div><p class="eyebrow">OPERATIONS OVERVIEW</p><h2>运营概览</h2></div>
      <button class="button ghost" @click="loadDashboard">刷新数据</button>
    </div>

    <div class="metric-grid">
      <button class="metric-card" @click="emit('open-list', {})"><span>工单总数</span><strong>{{ dashboard.summary.total }}</strong><small>全部模拟工单</small></button>
      <button class="metric-card" @click="emit('open-list', { status: 'RESOLVED' })"><span>解决率</span><strong>{{ dashboard.summary.resolution_rate }}%</strong><small>{{ dashboard.summary.resolved }} 条已解决/关闭</small></button>
      <button class="metric-card"><span>SLA达成率</span><strong>{{ dashboard.summary.sla_compliance_rate }}%</strong><small>已解决工单按时完成比例</small></button>
      <button class="metric-card"><span>平均处理时长</span><strong>{{ dashboard.summary.avg_resolution_hours }}h</strong><small>从创建到解决</small></button>
      <button class="metric-card warning" @click="emit('open-list', { sla: 'WARNING' })"><span>即将超时</span><strong>{{ dashboard.summary.warning }}</strong><small>已进入SLA预警区间</small></button>
      <button class="metric-card danger" @click="emit('open-list', { sla: 'OVERDUE' })"><span>超时未完成</span><strong>{{ dashboard.summary.overdue }}</strong><small>{{ dashboard.summary.escalated }} 条已升级处理</small></button>
    </div>

    <div class="chart-grid">
      <ChartCard title="近30天工单趋势" :option="trendOption" />
      <ChartCard title="工单状态分布" :option="pieOption(dashboard.by_status, statusLabels)" />
      <ChartCard title="问题类型分布" :option="categoryOption" />
      <ChartCard title="部门工单占比" :option="pieOption(dashboard.by_department)" />
    </div>
    <p class="data-note">数据更新时间：{{ new Date(dashboard.generated_at).toLocaleString() }}。当前展示内容均为模拟数据。</p>
  </div>
</template>
