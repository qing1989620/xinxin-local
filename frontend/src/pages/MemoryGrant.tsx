export default function MemoryGrant({
  permission,
  checked,
  disabled,
  onChange,
}: {
  permission: string;
  checked: boolean;
  disabled: boolean;
  onChange: (checked: boolean, permission: string) => void;
}) {
  return (
    <div className="memory-grant-field">
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={checked}
          disabled={disabled}
          aria-describedby="memory-grant-help"
          onChange={(event) =>
            onChange(
              event.target.checked,
              event.target.checked && permission === "read"
                ? "workspace"
                : permission,
            )
          }
        />
        允许 Agent 保存本轮明确提出的记忆
      </label>
      <p id="memory-grant-help" className="field-help">
        {disabled
          ? "本轮参数已固定，结束后可设置下一轮的记忆授权。"
          : permission === "read"
            ? "勾选时将本轮权限切换为工作区，允许保存文件和记忆，不包含系统命令执行。"
            : "当前权限允许保存记忆；只有你本轮明确要求记住的内容才会保存，可随时编辑、删除。"}
      </p>
    </div>
  );
}
