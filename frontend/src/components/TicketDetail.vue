<script setup>
import { computed, reactive, ref, watch } from "vue";
import { api } from "../api";

const props = defineProps({
  ticketId: { type: Number, required: true },
  meta: { type: Object, required: true },
  currentUser: { type: Object, required: true },
});
const emit = defineEmits(["close", "changed"]);
const detail = ref(null);
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const transition = reactive({ status: "", assignee_id: null, resolution: "", note: "" });
const agents = computed(() => props.meta.users.filter((user) => ["agent", "admin"].includes(user.role)));
const nextStatuses = computed(() => detail.value?.permissions?.allowed_transitions || []);
const statusLabels = { NEW: "待受理", ASSIGNED: "已分配", IN_PROGRESS: "处理中", RESOLVED: "已解决", CLOSED: "已关闭" };
const priorityLabels = { LOW: "低", MEDIUM: "中", HIGH: "高", URGENT: "紧急" };
const slaLabels = { ON_TRACK: "SLA正常", WARNING: "即将超时", OVERDUE: "已经超时", MET: "按时完成", BREACHED: "超时完成" };

async function load() {
  loading.value = true;
  error.value = "";
  try {
    detail.value = await api.getTicket(props.ticketId);
    transition.status = nextStatuses.value[0] || "";
    transition.assignee_id = detail.value.ticket.assignee_id || (props.currentUser.role === "agent" ? props.currentUser.id : agents.value[0]?.id);
    transition.resolution = detail.value.ticket.resolution || "";
    transition.note = "";
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

async function submitTransition() {
  saving.value = true;
  error.value = "";
  try {
    await api.transitionTicket(props.ticketId, { ...transition });
    await load();
    emit("changed");
  } catch (err) {
    error.value = err.message;
  } finally {
    saving.value = false;
  }
}

async function escalate() {
  saving.value = true;
  error.value = "";
  try {
    await api.escalateTicket(props.ticketId);
    await load();
    emit("changed");
  } catch (err) {
    error.value = err.message;
  } finally {
    saving.value = false;
  }
}

watch(() => props.ticketId, load, { immediate: true });
</script>

<template>
  <div class="drawer-backdrop" @click.self="emit('close')">
    <aside class="drawer">
      <button class="icon-button drawer-close" @click="emit('close')">×</button>
      <div v-if="loading" class="state-card">加载工单详情…</div>
      <div v-else-if="error && !detail" class="alert error">{{ error }}</div>
      <template v-else-if="detail">
        <p class="eyebrow">{{ detail.ticket.ticket_no }}</p>
        <h2>{{ detail.ticket.title }}</h2>
        <div class="tag-row">
          <span :class="['status-chip', detail.ticket.status.toLowerCase()]">{{ statusLabels[detail.ticket.status] }}</span>
          <span :class="['priority-chip', detail.ticket.priority.toLowerCase()]">{{ priorityLabels[detail.ticket.priority] }}</span>
          <span class="chip">{{ detail.ticket.category }}</span>
          <span :class="['sla-chip', detail.ticket.sla_status.toLowerCase()]">{{ slaLabels[detail.ticket.sla_status] }}</span>
          <span v-if="detail.ticket.escalation_level" class="escalation-chip">升级 L{{ detail.ticket.escalation_level }}</span>
        </div>
        <dl class="detail-grid">
          <div><dt>提交部门</dt><dd>{{ detail.ticket.department }}</dd></div><div><dt>提交人</dt><dd>{{ detail.ticket.requester_name }}</dd></div>
          <div><dt>负责人</dt><dd>{{ detail.ticket.assignee_name || "未分配" }}</dd></div><div><dt>创建时间</dt><dd>{{ new Date(detail.ticket.created_at).toLocaleString() }}</dd></div>
          <div><dt>SLA截止时间</dt><dd>{{ new Date(detail.ticket.due_at).toLocaleString() }}</dd></div><div><dt>SLA目标</dt><dd>{{ meta.sla_hours[detail.ticket.priority] }}小时</dd></div>
        </dl>
        <section class="detail-section"><h3>问题描述</h3><p>{{ detail.ticket.description }}</p></section>
        <section v-if="detail.ticket.resolution" class="detail-section success-box"><h3>解决方案</h3><p>{{ detail.ticket.resolution }}</p></section>

        <div v-if="detail.permissions.can_escalate" class="escalation-box"><div><strong>该工单已超过SLA期限</strong><small>管理员可将其升级，升级记录会写入操作日志。</small></div><button class="button danger-button" :disabled="saving || detail.ticket.escalation_level >= 3" @click="escalate">{{ detail.ticket.escalation_level >= 3 ? "已达最高级别" : "升级处理" }}</button></div>

        <form v-if="nextStatuses.length" class="transition-box" @submit.prevent="submitTransition">
          <h3>推进处理流程</h3>
          <div v-if="error" class="alert error">{{ error }}</div>
          <label class="field"><span>下一状态</span><select v-model="transition.status"><option v-for="item in nextStatuses" :key="item" :value="item">{{ statusLabels[item] }}</option></select></label>
          <label v-if="detail.permissions.can_assign" class="field"><span>负责人</span><select v-model.number="transition.assignee_id"><option v-for="user in agents" :key="user.id" :value="user.id">{{ user.name }}</option></select></label>
          <div v-else class="readonly-field"><span>操作身份</span><strong>{{ currentUser.name }} · {{ meta.role_labels[currentUser.role] }}</strong></div>
          <label v-if="transition.status === 'RESOLVED'" class="field"><span>解决方案</span><textarea v-model.trim="transition.resolution" rows="3" required placeholder="说明根因、处理动作和验证结果"></textarea></label>
          <label class="field"><span>处理备注</span><input v-model.trim="transition.note" placeholder="记录本次操作说明" /></label>
          <button class="button primary full" :disabled="saving">{{ saving ? "正在保存…" : "确认更新" }}</button>
        </form>
        <div v-else class="permission-note">当前角色对该工单没有可执行的状态操作。</div>

        <section class="detail-section"><h3>操作记录</h3><ol class="timeline"><li v-for="log in detail.logs" :key="log.id"><span></span><div><strong>{{ log.note }}</strong><small>{{ log.operator_name || "系统" }} · {{ new Date(log.created_at).toLocaleString() }}</small></div></li></ol></section>
      </template>
    </aside>
  </div>
</template>
