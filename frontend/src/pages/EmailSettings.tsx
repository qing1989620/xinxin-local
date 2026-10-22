import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  CheckCircle2,
  Globe,
  Loader2,
  Mail,
  Plus,
  Save,
  Send,
} from "lucide-react";
import { api, post, put } from "../api";
import { ErrorState, Loading, useResource, useToast } from "../ui";

type MailConfig = {
  email: string;
  provider: "smtp" | "resend";
  smtp_host: string;
  smtp_port: number;
  smtp_mode: string;
  smtp_username: string;
  resend_from: string;
  resend_configured: boolean;
  configured: boolean;
};

type DnsRecord = {
  record: string;
  name: string;
  type: string;
  value: string;
  ttl: string | number;
  priority: number | null;
  status: string;
};

type Domain = {
  id: string;
  name: string;
  status: string;
  region: string;
  created_at: string;
  records: DnsRecord[];
};

const STATUS_LABEL: Record<string, string> = {
  verified: "已验证",
  pending: "等待 DNS",
  not_started: "未开始",
  failure: "验证失败",
  temporary_failure: "暂时失败",
};

export default function EmailSettings() {
  const submitting = useRef(false);
  const { data, error, reload } = useResource<MailConfig>("/settings/email"),
    toast = useToast();
  const [form, setForm] = useState({
      email: "",
      provider: "smtp" as "smtp" | "resend",
      smtp_host: "smtp.qq.com",
      smtp_port: 465,
      smtp_mode: "ssl",
      smtp_username: "",
      smtp_password: "",
      resend_from: "",
      resend_api_key: "",
    }),
    [busy, setBusy] = useState(false),
    [testing, setTesting] = useState(false),
    [domains, setDomains] = useState<Domain[] | null>(null),
    [domainError, setDomainError] = useState(""),
    [domainBusy, setDomainBusy] = useState(""),
    [newDomain, setNewDomain] = useState("");
  useEffect(() => {
    if (data) {
      const { configured, resend_configured, ...values } = data;
      void configured;
      void resend_configured;
      setForm({ ...values, smtp_password: "", resend_api_key: "" });
    }
  }, [data]);
  async function loadDomains() {
    setDomainBusy("load");
    setDomainError("");
    try {
      const result = await api<{ domains: Domain[] }>(
        "/settings/email/domains",
      );
      setDomains(result.domains);
    } catch (failure) {
      setDomainError((failure as Error).message);
      setDomains(null);
    } finally {
      setDomainBusy("");
    }
  }
  useEffect(() => {
    if (form.provider === "resend" && data?.resend_configured)
      void loadDomains();
  }, [form.provider, data?.resend_configured]);
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  async function save(e: FormEvent) {
    e.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true);
    try {
      await put("/settings/email", form);
      setForm((v) => ({ ...v, smtp_password: "", resend_api_key: "" }));
      reload();
      toast(
        form.provider === "resend"
          ? "Resend 设置已保存；发送验证码时才会调用接口"
          : "SMTP 设置已保存；发送验证码时才会连接邮件服务",
      );
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  async function testDelivery() {
    setTesting(true);
    try {
      const result = await post<{ to: string; provider: string }>(
        "/settings/email/test",
        {},
      );
      toast(
        `测试邮件已发出，收件人 ${result.to}；几十秒内没收到就看一眼垃圾箱`,
      );
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setTesting(false);
    }
  }

  async function addDomain() {
    if (!newDomain.trim()) return;
    setDomainBusy("add");
    try {
      await post("/settings/email/domains", { name: newDomain.trim() });
      setNewDomain("");
      await loadDomains();
      toast("域名已添加，请按下方记录到 DNS 服务商处配置");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setDomainBusy("");
    }
  }
  async function verify(id: string) {
    setDomainBusy(id);
    try {
      await post(`/settings/email/domains/${id}/verify`, {});
      await loadDomains();
      toast("已触发验证，DNS 生效通常需要几分钟");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setDomainBusy("");
    }
  }
  return (
    <section className="settings-section" id="email">
      <div className="settings-intro">
        <Mail size={22} strokeWidth={1.3} />
        <h2>主人邮箱</h2>
        <p>
          用于验证码登录和找回密码。
          <br />
          只接受绑定邮箱，无公开注册。
        </p>
        <span className="subtle-badge">
          {data.configured
            ? data.provider === "resend"
              ? "Resend 已就绪"
              : "SMTP 授权已保存"
            : data.provider === "resend"
              ? "等待 Resend API Key"
              : "等待 SMTP 授权码"}
        </span>
      </div>
      <form className="form-stack settings-fields" onSubmit={save}>
        <fieldset
          className="form-fields"
          disabled={busy || testing || Boolean(domainBusy)}
        >
          <div className="provider-switch" role="group" aria-label="发送方式">
            <button
              type="button"
              className={form.provider === "smtp" ? "active" : ""}
              aria-pressed={form.provider === "smtp"}
              disabled={busy || testing || Boolean(domainBusy)}
              onClick={() => setForm({ ...form, provider: "smtp" })}
            >
              SMTP 授权码
            </button>
            <button
              type="button"
              className={form.provider === "resend" ? "active" : ""}
              aria-pressed={form.provider === "resend"}
              disabled={busy || testing || Boolean(domainBusy)}
              onClick={() => setForm({ ...form, provider: "resend" })}
            >
              Resend API
            </button>
          </div>
          <label>
            绑定邮箱
            <input
              type="email"
              value={form.email}
              required
              maxLength={254}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </label>
          {form.provider === "smtp" ? (
            <>
              <div className="form-columns">
                <label>
                  SMTP 服务器
                  <input
                    value={form.smtp_host}
                    required
                    onChange={(e) =>
                      setForm({ ...form, smtp_host: e.target.value })
                    }
                  />
                </label>
                <label>
                  端口
                  <input
                    type="number"
                    min={1}
                    max={65535}
                    value={form.smtp_port}
                    required
                    onChange={(e) =>
                      setForm({ ...form, smtp_port: Number(e.target.value) })
                    }
                  />
                </label>
              </div>
              <label>
                加密方式
                <select
                  value={form.smtp_mode}
                  onChange={(e) =>
                    setForm({ ...form, smtp_mode: e.target.value })
                  }
                >
                  <option value="ssl">SSL / TLS（QQ 邮箱使用 465）</option>
                  <option value="starttls">STARTTLS（通常使用 587）</option>
                </select>
              </label>
              <label>
                SMTP 登录邮箱
                <input
                  type="email"
                  value={form.smtp_username}
                  placeholder="留空使用绑定邮箱"
                  onChange={(e) =>
                    setForm({ ...form, smtp_username: e.target.value })
                  }
                />
              </label>
              <label>
                SMTP 授权码
                <input
                  type="password"
                  autoComplete="new-password"
                  value={form.smtp_password}
                  placeholder={
                    data.configured
                      ? "留空保留已保存授权码"
                      : "QQ 邮箱设置中获取的 SMTP 授权码"
                  }
                  onChange={(e) =>
                    setForm({ ...form, smtp_password: e.target.value })
                  }
                />
              </label>
            </>
          ) : (
            <>
              <label>
                Resend API Key
                <input
                  type="password"
                  autoComplete="new-password"
                  value={form.resend_api_key}
                  placeholder={
                    data.resend_configured
                      ? "留空保留已保存的 Key"
                      : "re_…（Resend 控制台 API Keys）"
                  }
                  onChange={(e) =>
                    setForm({ ...form, resend_api_key: e.target.value })
                  }
                />
              </label>
              <label>
                发件人
                <input
                  value={form.resend_from}
                  placeholder="Xinxin <no-reply@your-domain.com>"
                  onChange={(e) =>
                    setForm({ ...form, resend_from: e.target.value })
                  }
                />
              </label>
              <p className="field-help">
                Resend 免费额度约每天 100 封、每月 3000 封。发件域名需要在下方
                通过 DNS 验证；未验证前只能发往账号本人邮箱。
              </p>
              <div className="domain-block">
                <div className="domain-head">
                  <strong>
                    <Globe size={14} /> 发件域名
                  </strong>
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => void loadDomains()}
                    disabled={!data.resend_configured || domainBusy === "load"}
                  >
                    {domainBusy === "load" ? (
                      <Loader2 size={13} className="spin" />
                    ) : (
                      <CheckCircle2 size={13} />
                    )}
                    刷新列表
                  </button>
                </div>
                {!data.resend_configured && (
                  <p className="field-help">
                    先保存 API Key，才能读取和添加域名。
                  </p>
                )}
                {domainError && (
                  <p className="form-error" role="alert">
                    {domainError}
                  </p>
                )}
                {domains?.length ? (
                  <div className="domain-list">
                    {domains.map((domain) => (
                      <div className="domain-row" key={domain.id}>
                        <div className="domain-head">
                          <strong>{domain.name}</strong>
                          <span
                            className={`domain-status ${domain.status === "verified" ? "verified" : ""}`}
                          >
                            {STATUS_LABEL[domain.status] || domain.status}
                          </span>
                          {domain.status === "verified" ? (
                            <button
                              type="button"
                              className="text-button"
                              onClick={() =>
                                setForm({
                                  ...form,
                                  resend_from: `Xinxin <no-reply@${domain.name}>`,
                                })
                              }
                            >
                              用于发件
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="text-button"
                              disabled={domainBusy === domain.id}
                              onClick={() => void verify(domain.id)}
                            >
                              {domainBusy === domain.id ? "验证中…" : "验证"}
                            </button>
                          )}
                        </div>
                        {domain.status !== "verified" &&
                          domain.records?.length > 0 && (
                            <div className="domain-records">
                              {domain.records.map((record) => (
                                <div
                                  key={`${record.type}-${record.name}-${record.value}`}
                                >
                                  {record.record || record.type} · {record.name}{" "}
                                  · {record.type}
                                  <br />
                                  <code>{record.value}</code>
                                </div>
                              ))}
                            </div>
                          )}
                      </div>
                    ))}
                  </div>
                ) : (
                  data.resend_configured &&
                  domains && (
                    <p className="field-help">还没有域名，在下面添加一个。</p>
                  )
                )}
                <div className="domain-add">
                  <input
                    value={newDomain}
                    placeholder="your-domain.com"
                    onChange={(e) => setNewDomain(e.target.value)}
                    disabled={!data.resend_configured}
                  />
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => void addDomain()}
                    disabled={!data.resend_configured || domainBusy === "add"}
                  >
                    <Plus size={14} />
                    {domainBusy === "add" ? "添加中…" : "添加域名"}
                  </button>
                </div>
              </div>
            </>
          )}
          <p className="field-help">
            6 位验证码，10 分钟有效，60 秒发送间隔。凭据只在后端加密保存，
            接口永远不会回显。
          </p>
          <div className="email-actions">
            <button className="button secondary" disabled={busy}>
              <Save size={15} />
              {busy ? "正在保存…" : "保存邮箱设置"}
            </button>
            <button
              type="button"
              className="button secondary"
              onClick={() => void testDelivery()}
              disabled={!data.configured || testing}
              title={
                data.configured
                  ? "发一封测试邮件到绑定邮箱"
                  : "先保存完整的发信配置"
              }
            >
              {testing ? (
                <Loader2 size={15} className="spin" />
              ) : (
                <Send size={15} />
              )}
              {testing ? "正在发送…" : "发送测试邮件"}
            </button>
          </div>
        </fieldset>
      </form>
    </section>
  );
}
