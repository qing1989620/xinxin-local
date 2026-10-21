/** 极小的函数表达式解析器：只支持画图需要的语法，不使用 eval。
 *
 *  支持：数字、x、常量 pi/e、+ - * / ^（右结合）、括号、一元负号、
 *  隐式乘法（2x、3sin(x)）、单参/双参函数。
 *  出错时返回 ok:false，由调用方决定怎么提示。
 */

type Token =
  | { kind: "num"; value: number }
  | { kind: "name"; value: string }
  | { kind: "op"; value: string }
  | { kind: "lp" }
  | { kind: "rp" }
  | { kind: "comma" };

export type CompiledExpression =
  | { ok: true; source: string; evaluate: (x: number) => number }
  | { ok: false; source: string; error: string };

const CONSTANTS: Record<string, number> = {
  pi: Math.PI,
  π: Math.PI,
  e: Math.E,
  tau: Math.PI * 2,
};

const UNARY: Record<string, (value: number) => number> = {
  sin: Math.sin,
  cos: Math.cos,
  tan: Math.tan,
  asin: Math.asin,
  acos: Math.acos,
  atan: Math.atan,
  sinh: Math.sinh,
  cosh: Math.cosh,
  tanh: Math.tanh,
  exp: Math.exp,
  ln: Math.log,
  log: Math.log10,
  lg: Math.log10,
  log2: Math.log2,
  log10: Math.log10,
  sqrt: Math.sqrt,
  cbrt: Math.cbrt,
  abs: Math.abs,
  floor: Math.floor,
  ceil: Math.ceil,
  round: Math.round,
  sign: Math.sign,
};

const BINARY: Record<string, (a: number, b: number) => number> = {
  min: Math.min,
  max: Math.max,
  atan2: Math.atan2,
  pow: Math.pow,
  mod: (a, b) => a % b,
};

function tokenize(input: string): Token[] {
  const tokens: Token[] = [];
  let index = 0;
  while (index < input.length) {
    const char = input[index];
    if (char === " " || char === "\t" || char === "\n") {
      index += 1;
      continue;
    }
    if (char === "π") {
      tokens.push({ kind: "name", value: "π" });
      index += 1;
      continue;
    }
    if (/[0-9.]/.test(char)) {
      let end = index;
      while (end < input.length && /[0-9.]/.test(input[end])) end += 1;
      // 科学计数法：1e-3
      if (input[end] === "e" && /[+-]?\d/.test(input.slice(end + 1, end + 2))) {
        end += 1;
        if (input[end] === "+" || input[end] === "-") end += 1;
        while (end < input.length && /[0-9]/.test(input[end])) end += 1;
      }
      const value = Number(input.slice(index, end));
      if (!Number.isFinite(value)) throw new Error("数字写错了");
      tokens.push({ kind: "num", value });
      index = end;
      continue;
    }
    if (/[a-zA-Z_]/.test(char)) {
      let end = index;
      while (end < input.length && /[a-zA-Z_0-9]/.test(input[end])) end += 1;
      tokens.push({ kind: "name", value: input.slice(index, end).toLowerCase() });
      index = end;
      continue;
    }
    if (char === "(") {
      tokens.push({ kind: "lp" });
      index += 1;
      continue;
    }
    if (char === ")") {
      tokens.push({ kind: "rp" });
      index += 1;
      continue;
    }
    if (char === "," || char === "，") {
      tokens.push({ kind: "comma" });
      index += 1;
      continue;
    }
    if ("+-*/^".includes(char)) {
      tokens.push({ kind: "op", value: char });
      index += 1;
      continue;
    }
    if (char === "×" || char === "·") {
      tokens.push({ kind: "op", value: "*" });
      index += 1;
      continue;
    }
    if (char === "÷") {
      tokens.push({ kind: "op", value: "/" });
      index += 1;
      continue;
    }
    throw new Error(`看不懂这个符号：${char}`);
  }
  return tokens;
}

/** 递归下降：expr → term → unary → power → primary，隐式乘法在 term 里处理。 */
class Parser {
  private position = 0;

  constructor(private readonly tokens: Token[]) {}

  private peek(): Token | undefined {
    return this.tokens[this.position];
  }

  private eat(kind: Token["kind"]): Token | undefined {
    const token = this.peek();
    if (token && token.kind === kind) {
      this.position += 1;
      return token;
    }
    return undefined;
  }

  parse(): (x: number) => number {
    const node = this.expression();
    if (this.position < this.tokens.length) throw new Error("表达式没写完");
    return node;
  }

  private expression(): (x: number) => number {
    let left = this.term();
    while (true) {
      const token = this.peek();
      if (token && token.kind === "op" && (token.value === "+" || token.value === "-")) {
        this.position += 1;
        const right = this.term();
        const previous = left;
        left =
          token.value === "+"
            ? (x) => previous(x) + right(x)
            : (x) => previous(x) - right(x);
        continue;
      }
      return left;
    }
  }

  private term(): (x: number) => number {
    let left = this.unary();
    while (true) {
      const token = this.peek();
      if (token && token.kind === "op" && (token.value === "*" || token.value === "/")) {
        this.position += 1;
        const right = this.unary();
        const previous = left;
        left =
          token.value === "*"
            ? (x) => previous(x) * right(x)
            : (x) => previous(x) / right(x);
        continue;
      }
      // 隐式乘法：2x、3sin(x)、(x+2)(x-3)
      if (token && (token.kind === "num" || token.kind === "name" || token.kind === "lp")) {
        const right = this.unary();
        const previous = left;
        left = (x) => previous(x) * right(x);
        continue;
      }
      return left;
    }
  }

  private unary(): (x: number) => number {
    const token = this.peek();
    if (token && token.kind === "op" && (token.value === "-" || token.value === "+")) {
      this.position += 1;
      const operand = this.unary();
      return token.value === "-" ? (x) => -operand(x) : operand;
    }
    return this.power();
  }

  private power(): (x: number) => number {
    const base = this.primary();
    const token = this.peek();
    if (token && token.kind === "op" && token.value === "^") {
      this.position += 1;
      const exponent = this.unary();
      return (x) => base(x) ** exponent(x);
    }
    return base;
  }

  private primary(): (x: number) => number {
    const token = this.peek();
    if (!token) throw new Error("表达式不完整");
    if (token.kind === "num") {
      this.position += 1;
      const value = token.value;
      return () => value;
    }
    if (token.kind === "lp") {
      this.position += 1;
      const inner = this.expression();
      if (!this.eat("rp")) throw new Error("括号没闭合");
      return inner;
    }
    if (token.kind === "name") {
      this.position += 1;
      const name = token.value;
      if (name === "x") return (value) => value;
      if (name in CONSTANTS) {
        const value = CONSTANTS[name];
        return () => value;
      }
      if (this.eat("lp")) {
        const args: Array<(x: number) => number> = [];
        if (!this.eat("rp")) {
          do {
            args.push(this.expression());
          } while (this.eat("comma"));
          if (!this.eat("rp")) throw new Error("括号没闭合");
        }
        if (name in UNARY && args.length === 1) {
          const fn = UNARY[name];
          const inner = args[0];
          return (x) => fn(inner(x));
        }
        if (name in BINARY && args.length === 2) {
          const fn = BINARY[name];
          const first = args[0];
          const second = args[1];
          return (x) => fn(first(x), second(x));
        }
        throw new Error(`函数 ${name} 的参数不对`);
      }
      throw new Error(`不认识 ${name}`);
    }
    throw new Error("表达式不完整");
  }
}

/** 去掉 "y ="、"f(x) =" 这类前缀，保留纯表达式。 */
export function stripAssignment(raw: string): string {
  return (raw || "")
    .replace(/^\s*(?:y|f\s*\(\s*x\s*\))\s*=/i, "")
    .trim();
}

export function compileExpression(raw: string): CompiledExpression {
  const source = stripAssignment(raw);
  if (!source) return { ok: false, source, error: "表达式为空" };
  try {
    const evaluate = new Parser(tokenize(source)).parse();
    return {
      ok: true,
      source,
      evaluate: (x: number) => {
        const value = evaluate(x);
        return Number.isFinite(value) ? value : Number.NaN;
      },
    };
  } catch (error) {
    return {
      ok: false,
      source,
      error: error instanceof Error ? error.message : "表达式无法解析",
    };
  }
}

/** 从一段文本里拆出多行表达式（用换行或分号分隔）。 */
export function splitExpressions(raw: string): string[] {
  return (raw || "")
    .split(/[\n;；]+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 4);
}
