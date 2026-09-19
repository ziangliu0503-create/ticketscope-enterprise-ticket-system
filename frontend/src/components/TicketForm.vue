<script setup>
import { reactive, ref } from "vue";
import { api } from "../api";

const props = defineProps({ meta: { type: Object, required: true } });
const emit = defineEmits(["created", "cancel"]);
const saving = ref(false);
const error = ref("");
const requesters = props.meta.users.filter((user) => user.role === "requester");
const form = reactive({
  title: "",
  description: "",
  department: requesters[0]?.department || props.meta.departments[0],
  category: props.meta.categories[0],
  priority: "MEDIUM",
  requester_id: requesters[0]?.id,
});

async function submit() {
  saving.value = true;
  error.value = "";
  try {
    const created = await api.createTicket(form);
    emit("created", created);
  } catch (err) {
    error.value = err.message;
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('cancel')">
    <form class="modal" @submit.prevent="submit">
      <div class="modal-header"><div><p class="eyebrow">NEW TICKET</p><h2>创建工单</h2></div><button type="button" class="icon-button" @click="emit('cancel')">×</button></div>
      <div v-if="error" class="alert error">{{ error }}</div>
      <label class="field field-wide"><span>问题标题</span><input v-model.trim="form.title" required maxlength="80" placeholder="简要描述问题" /></label>
      <label class="field field-wide"><span>问题描述</span><textarea v-model.trim="form.description" required rows="4" placeholder="说明出现时间、影响范围和已尝试的处理方式"></textarea></label>
      <div class="form-grid">
        <label class="field"><span>提交人</span><select v-model.number="form.requester_id"><option v-for="user in requesters" :key="user.id" :value="user.id">{{ user.name }} · {{ user.department }}</option></select></label>
        <label class="field"><span>提交部门</span><select v-model="form.department"><option v-for="item in meta.departments" :key="item">{{ item }}</option></select></label>
        <label class="field"><span>问题类型</span><select v-model="form.category"><option v-for="item in meta.categories" :key="item">{{ item }}</option></select></label>
        <label class="field"><span>优先级</span><select v-model="form.priority"><option value="LOW">低</option><option value="MEDIUM">中</option><option value="HIGH">高</option><option value="URGENT">紧急</option></select></label>
      </div>
      <div class="modal-actions"><button type="button" class="button ghost" @click="emit('cancel')">取消</button><button class="button primary" :disabled="saving">{{ saving ? "正在提交…" : "创建工单" }}</button></div>
    </form>
  </div>
</template>

