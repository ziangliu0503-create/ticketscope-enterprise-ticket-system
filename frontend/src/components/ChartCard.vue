<script setup>
import * as echarts from "echarts";
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  option: { type: Object, required: true },
});

const chartElement = ref(null);
let chart;
let observer;

function render() {
  if (!chartElement.value) return;
  if (!chart) chart = echarts.init(chartElement.value);
  chart.setOption(props.option, true);
}

onMounted(async () => {
  await nextTick();
  render();
  observer = new ResizeObserver(() => chart?.resize());
  observer.observe(chartElement.value);
});

watch(() => props.option, render, { deep: true });

onBeforeUnmount(() => {
  observer?.disconnect();
  chart?.dispose();
});
</script>

<template>
  <section class="panel chart-panel">
    <header class="panel-header"><h3>{{ title }}</h3></header>
    <div ref="chartElement" class="chart"></div>
  </section>
</template>

