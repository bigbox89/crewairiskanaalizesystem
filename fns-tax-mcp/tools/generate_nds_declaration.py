"""Генерация декларации по НДС."""
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
    name="generate_nds_declaration",
    description="""Генерирует готовую к отправке декларацию по НДС.
Возвращает XML + человекочитаемый отчёт + сумму НДС к уплате/возмещению.
Соответствует формату ФНС (КНД 1151001, версия 5.10).""",
)
async def generate_nds_declaration(
    inn: str = Field(..., description="ИНН налогоплательщика (10 или 12 цифр)"),
    period: Literal["Q1", "Q2", "Q3", "Q4", "YEAR"] = Field(..., description="Период: Q1-Q4 или YEAR"),
    year: int = Field(..., description="Год, например 2025"),
    turnover: float = Field(..., description="Оборот за период (руб.)"),
    nds_to_pay: float = Field(0.0, description="Сумма НДС к уплате (руб.)"),
    nds_to_refund: float = Field(0.0, description="Сумма НДС к возмещению (руб.)"),
    ctx: Context = None
) -> ToolResult:
    """Генерирует декларацию НДС локально в формате XML по стандартам ФНС."""
    
    if not validate_inn(inn):
        raise McpError(ErrorData(code=-32602, message="ИНН должен содержать 10 или 12 цифр"))
    
    
    with tracer.start_as_current_span("generate_nds_declaration") as span:
        span.set_attribute("inn", inn)
        span.set_attribute("period", period)
        span.set_attribute("year", year)
        
        
        await ctx.info("🚀 Начинаем генерацию декларации НДС")
        await ctx.report_progress(progress=0, total=100)
        
        
        await ctx.info("📝 Генерируем XML декларацию по формату ФНС (КНД 1151001)")
        await ctx.report_progress(progress=50, total=100)
        
        try:
            # Генерация XML через xml_generator
            xml_content = DeclarationXMLGenerator.generate_nds_xml(
                inn=inn,
                period=period,
                year=year,
                nds_to_pay=nds_to_pay,
                nds_to_refund=nds_to_refund,
                turnover=turnover
            )
            
            
            human_text = f"""
Декларация НДС за {period} {year}
ИНН: {inn}
Оборот: {turnover:,.2f} ₽
НДС к уплате: {nds_to_pay:,.2f} ₽
НДС к возмещению: {nds_to_refund:,.2f} ₽
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
                    "nds_to_pay": nds_to_pay,
                    "nds_to_refund": nds_to_refund,
                    "turnover": turnover,
                    "declaration_xml": xml_content,
                    "status": "generated",
                    "format": "КНД 1151001",
                    "version": "5.10"
                },
                meta={"nds_to_pay": nds_to_pay, "nds_to_refund": nds_to_refund, "declaration_type": "NDS"}
            )
        
        except Exception as e:
            
            await ctx.error(f"❌ Ошибка генерации декларации: {e}")
            raise McpError(ErrorData(code=-32603, message=f"Не удалось сгенерировать декларацию: {e}"))

