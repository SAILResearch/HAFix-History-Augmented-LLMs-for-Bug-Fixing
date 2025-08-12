public final Object computeValue(EvalContext context) {
    #<BUGGY_LINE>
    return compute(args[0].computeValue(context), args[1].computeValue(context)) ? Boolean.TRUE : Boolean.FALSE;
    #<BUGGY_LINE>
}