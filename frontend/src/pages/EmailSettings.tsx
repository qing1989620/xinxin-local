import { useEffect, useState, type FormEvent } from "react";
import { Mail, Save } from "lucide-react";
import { put } from "../api";
import { ErrorState, Loading, useResource, useToast } from "../ui";
type MailConfig = {
  email: string;
  smtp_host: string;
  smtp_port: number;
  smtp_mode: string;
  smtp_username: string;
  configured: boolean;
};
export default function EmailSettings() {
  const { data, error, reload } = useResource<MailConfig>("/settings/email"),
    toast = useToast();
  const [form, setForm] = useState({
      email: "",
      smtp_host: "smtp.qq.com",
      smtp_port: 465,
      smtp_mode: "ssl",
      smtp_username: "",
      smtp_password: "",
    }),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    if (data) {
      const { configured, ...values } = data;
      setForm({ ...values, smtp_password: "" });
    }
  }, [data]);
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await put("/settings/email", form);
      setForm((v) => ({ ...v, smtp_password: "" }));
      reload();
      toast("邮箱设置已保存；发送验证码时才会连接邮件服务");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="settings-section">
      <div className="settings-intro">
        <Mail size={22} strokeWidth={1.3} />
        <h2>主人邮箱</h2>
        <p>
          用于验证码登录和找回密码。
          <br />
          只接受绑定邮箱，无公开注册。
        </p>
        <span className="subtle-badge">
          {data.configured ? "SMTP 授权已保存" : "等待 SMTP 授权码"}
        </span>
      </div>
      <form className="form-stack settings-fields" onSubmit={save}>
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
        <div className="form-columns">
          <label>
            SMTP 服务器
            <input
              value={form.smtp_host}
              required
              onChange={(e) => setForm({ ...form, smtp_host: e.target.value })}
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
            onChange={(e) => setForm({ ...form, smtp_mode: e.target.value })}
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
        <p className="field-help">
          6 位验证码，10 分钟有效，60
          秒发送间隔。授权码只在后端加密保存。当前不会自动发送邮件。
        </p>
        <button className="button secondary" disabled={busy}>
          <Save size={15} />
          {busy ? "正在保存…" : "保存邮箱设置"}
        </button>
      </form>
    </section>
  );
}
