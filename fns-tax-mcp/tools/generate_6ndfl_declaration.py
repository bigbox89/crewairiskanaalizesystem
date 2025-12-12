"""Генерация формы 6-НДФЛ."""
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
    name="generate_6ndfl_declaration",
    description="""Генерирует готовую к отправке форму 6-НДФЛ.
Возвращает XML + человекочитаемый отчёт + суммы НДФЛ.
Соответствует формату ФНС (КНД 1151078, версия 5.10).""",
)
async def generate_6ndfl_declaration(
    inn: str = Field(..., description="ИНН налогоплательщика (10 или 12 цифр)"),
    period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"] = Field(..., description="Период: Q1-Q4 или YEAR"),
    year: int = Field(..., description="Год, например 2025"),
    total_income: float = Field(..., description="Общая сумма доходов физических лиц (руб.)"),
    total_ndfl: float = Field(..., description="Общая сумма начисленного НДФЛ (руб.)"),
    withheld_ndfl: float = Field(..., description="Сумма удержанного НДФЛ (руб.)"),
    ctx: Context = None
) -> ToolResult:
    """Генерирует форму 6-НДФЛ локально в формате XML по стандартам ФНС."""
    
    if not validate_inn(inn):
        raise McpError(ErrorData(code=-32602, message="ИНН должен содержать 10 или 12 цифр"))
    
    
    with tracer.start_as_current_span("generate_6ndfl_declaration") as span:
        span.set_attribute("inn", inn)
        span.set_attribute("period", period)
        span.set_attribute("year", year)
        
        
        await ctx.info("🚀 Начинаем генерацию формы 6-НДФЛ")
        await ctx.report_progress(progress=0, total=100)
        
        
        await ctx.info("📝 Генерируем XML форму по формату ФНС (КНД 1151078)")
        await ctx.report_progress(progress=50, total=100)
        
        try:
            # Генерация XML через xml_generator
            xml_content = DeclarationXMLGenerator.generate_6ndfl_xml(
                inn=inn,
                period=period,
                year=year,
                total_income=total_income,
                total_ndfl=total_ndfl,
                withheld_ndfl=withheld_ndfl
            )
            
            
            human_text = f"""
Форма 6-НДФЛ за {period} {year}
ИНН: {inn}
Общая сумма доходов: {total_income:,.2f} ₽
Начислено НДФЛ: {total_ndfl:,.2f} ₽
Удержано НДФЛ: {withheld_ndfl:,.2f} ₽
XML форма сгенерирована по формату ФНС (КНД 1151078)
""".strip()
            
            await ctx.report_progress(progress=100, total=100)
            await ctx.info("✅ Форма успешно сгенерирована")
            
            
            return ToolResult(
                content=[TextContent(type="text", text=human_text)],
                structured_content={
                    "inn": inn,
                    "period": period,
                    "year": year,
                    "total_income": total_income,
                    "total_ndfl": total_ndfl,
                    "withheld_ndfl": withheld_ndfl,
                    "declaration_xml": xml_content,
                    "status": "generated",
                    "format": "КНД 1151078",
                    "version": "5.10"
                },
                meta={"total_ndfl": total_ndfl, "withheld_ndfl": withheld_ndfl, "declaration_type": "6NDFL"}
            )
        
        except Exception as e:
            
            await ctx.error(f"❌ Ошибка генерации формы: {e}")
            raise McpError(ErrorData(code=-32603, message=f"Не удалось сгенерировать форму: {e}"))

