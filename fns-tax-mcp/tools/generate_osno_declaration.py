"""Генерация декларации по ОСНО."""
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
    name="generate_osno_declaration",
    description="""Генерирует готовую к отправке декларацию по ОСНО.
Возвращает XML + человекочитаемый отчёт + сумму налога к уплате.""",
)
async def generate_osno_declaration(
    inn: str = Field(..., description="ИНН налогоплательщика (10 или 12 цифр)"),
    period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"] = Field(..., description="Период: Q1-Q4 или YEAR"),
    year: int = Field(..., description="Год, например 2025"),
    income: float = Field(..., description="Доходы за период (руб.)"),
    profit: float = Field(..., description="Прибыль за период (руб.)"),
    expenses: float = Field(0.0, description="Расходы за период (руб.)"),
    loss: float = Field(0.0, description="Убыток за период (руб.)"),
    nds: float = Field(0.0, description="НДС к уплате (руб.)"),
    ctx: Context = None
) -> ToolResult:
    """Генерирует декларацию ОСНО локально в формате XML по стандартам ФНС."""
    
    if not validate_inn(inn):
        raise McpError(ErrorData(code=-32602, message="ИНН должен содержать 10 или 12 цифр"))
    
    
    with tracer.start_as_current_span("generate_osno_declaration") as span:
        span.set_attribute("inn", inn)
        span.set_attribute("period", period)
        span.set_attribute("year", year)
        
        
        await ctx.info("🚀 Начинаем генерацию декларации ОСНО")
        await ctx.report_progress(progress=0, total=100)
        
        
        await ctx.info("📝 Генерируем XML декларацию по формату ФНС (КНД 1151001)")
        await ctx.report_progress(progress=50, total=100)
        
        try:
            # Генерация XML через xml_generator
            xml_content = DeclarationXMLGenerator.generate_osno_xml(
                inn=inn,
                period=period,
                year=year,
                income=income,
                expenses=expenses,
                profit=profit,
                loss=loss,
                nds=nds
            )
            
            # Расчет суммы налога на прибыль (20%)
            tax_amount = profit * 0.20
            
            
            human_text = f"""
Декларация ОСНО за {period} {year}
ИНН: {inn}
Доходы: {income:,.2f} ₽
Расходы: {expenses:,.2f} ₽
Прибыль: {profit:,.2f} ₽
Убыток: {loss:,.2f} ₽
НДС к уплате: {nds:,.2f} ₽
Налог на прибыль к уплате: {tax_amount:,.2f} ₽
XML декларация сгенерирована по формату ФНС (КНД 1151001)
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
                    "profit": profit,
                    "loss": loss,
                    "nds": nds,
                    "tax_amount": tax_amount,
                    "declaration_xml": xml_content,
                    "status": "generated",
                    "format": "КНД 1151001",
                    "version": "5.10"
                },
                meta={"tax_amount": tax_amount, "declaration_type": "OSNO"}
            )
        
        except Exception as e:
            
            await ctx.error(f"❌ Ошибка генерации декларации: {e}")
            raise McpError(ErrorData(code=-32603, message=f"Не удалось сгенерировать декларацию: {e}"))

