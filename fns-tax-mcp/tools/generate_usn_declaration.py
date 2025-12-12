"""Генерация декларации по УСН (6% или 15%)."""
from typing import Literal
from fastmcp import Context
from mcp.types import TextContent
from opentelemetry import trace
from pydantic import Field
from mcp_instance import mcp
from .utils import ToolResult, validate_inn
from mcp.shared.exceptions import McpError, ErrorData
from .xml_generator import DeclarationXMLGenerator

tracer = trace.get_tracer(__name__)


@mcp.tool(
    name="generate_usn_declaration",
    description="""Генерирует готовую к отправке декларацию по УСН.
Поддерживает УСН «Доходы» (6%) и УСН «Доходы минус расходы» (15%).
Возвращает XML + человекочитаемый отчёт + сумму налога к уплате.""",
)
async def generate_usn_declaration(
    inn: str = Field(..., description="ИНН налогоплательщика (10 или 12 цифр)"),
    period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"] = Field(..., description="Период: Q1-Q4 или YEAR"),
    year: int = Field(..., description="Год, например 2025"),
    income: float = Field(..., description="Доходы за период (руб.)"),
    expenses: float = Field(0.0, description="Расходы за период (только для УСН 15%)"),
    tax_rate: Literal[6, 15] = Field(6, description="Ставка налога: 6 или 15"),
    ctx: Context = None
) -> ToolResult:
    """Генерирует декларацию УСН локально в формате XML по стандартам ФНС."""
    if not validate_inn(inn):
        raise McpError(ErrorData(code=-32602, message="ИНН должен содержать 10 или 12 цифр"))
    
    with tracer.start_as_current_span("generate_usn_declaration") as span:
        span.set_attribute("inn", inn)
        span.set_attribute("period", period)
        span.set_attribute("tax_rate", tax_rate)
        span.set_attribute("year", year)
        
        await ctx.info("🚀 Начинаем генерацию декларации УСН")
        await ctx.report_progress(progress=0, total=100)
        
        await ctx.info("📝 Генерируем XML декларацию по формату ФНС (КНД 1152017)")
        await ctx.report_progress(progress=50, total=100)
        
        try:
            xml_content = DeclarationXMLGenerator.generate_usn_xml(
                inn=inn,
                period=period,
                year=year,
                income=income,
                expenses=expenses,
                tax_rate=tax_rate
            )
            
            # Расчет суммы налога
            if tax_rate == 6:
                tax_amount = income * 0.06
            else:
                tax_base = income - expenses
                tax_amount = tax_base * 0.15 if tax_base > 0 else 0.0
            
            human_text = f"""
Декларация УСН {tax_rate}% за {period} {year}
ИНН: {inn}
Доходы: {income:,.2f} ₽
Расходы: {expenses:,.2f} ₽
Налог к уплате: {tax_amount:,.2f} ₽
XML декларация сгенерирована по формату ФНС (КНД 1152017)
""".strip()
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Декларация успешно сгенерирована")
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text)],
                structured_content={
                    "inn": inn,
                    "period": period,
                    "year": year,
                    "income": income,
                    "expenses": expenses,
                    "tax_rate": tax_rate,
                    "tax_amount": tax_amount,
                    "declaration_xml": xml_content,
                    "status": "generated",
                    "format": "КНД 1152017",
                    "version": "5.05"
                },
                meta={"tax_amount": tax_amount, "declaration_type": f"USN_{tax_rate}"}
            )
        
        except Exception as e:
            await ctx.error(f"❌ Ошибка генерации декларации: {e}")
            raise McpError(ErrorData(code=-32603, message=f"Не удалось сгенерировать декларацию: {e}"))

